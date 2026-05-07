import logging
import random
from typing import Dict, Any
from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from users.models import User, OTPCode
from services.tasks import send_welcome_email_task, send_otp_email_task

logger = logging.getLogger("api.users")

def _get_token_pair(user: User) -> tuple[str, str]:
    """
    Helper: Build token pair for a user
    """
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    return str(access), str(refresh)

def _generate_otp(*, user: User) -> OTPCode:
    """
    Generate a new OTP for a user.

    Rules:
    - Delete existing OTP if present
    - Generate a random 6-digit code
    - Save and return OTPCode
    """
    OTPCode.objects.filter(user=user).delete()

    code = f"{random.randint(100000, 999999):06d}"
    otp = OTPCode.objects.create(user=user, code=code)

    logger.info("OTP generated", extra={"user_id": user.id})
    return otp

def verify_otp(*, email: str, code: str) -> tuple[User, str, str]:
    """
    Verify OTP and activate user.

    Rules:
    - User must exist
    - OTP must exist and match
    - OTP must not be expired
    - Activate user and delete OTP atomically
    - Return JWT tokens
    """
    try:
        user = User.objects.get(email=email)
        otp = OTPCode.objects.get(user=user)
    except (User.DoesNotExist, OTPCode.DoesNotExist):
        raise ValueError("Invalid email or code")
    
    if otp.is_expired():
        otp.delete()
        raise ValueError("OTP has expired, please request for a new one")
    
    if code != otp.code:
        raise ValueError("Invalid email or code")
    
    with transaction.atomic():
        user.is_active = True
        user.save()
        otp.delete()
    
    send_welcome_email_task.delay(user.id)
    logger.info("OTP verified, user activated", extra={"user_id": user.id})
    access, refresh = _get_token_pair(user)
    return user, access, refresh

def resend_otp(*, email: str) -> None:
    """
    Resend OTP to user.

    Rules:
    - User must exist
    - User must not already be verified
    - Delete old OTP, generate new one
    """
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise ValueError("Invalid email")
    
    if user.is_active:
        raise ValueError("User already verified")
    
    otp = _generate_otp(user=user)
    send_otp_email_task.delay(user.id, otp.code)

    logger.info("OTP resent", extra={"user_id": user.id})

def register_user(*, data: Dict[str, Any]) -> None:
    """
    Create a new user account.

    Rules:
    - email must be unique
    - password is hashed before storage
    - user is inactive until email is verified
    - OTP is generated and emailed
    """
    try:
        password = data.pop("password")
        user = User.objects.create_user(**data, password=password, is_active=False)
    except IntegrityError:
        logger.warning("Registration failed - duplicate email", extra={"email": data.get("email")})
        raise ValueError("A user with this email already exists")
    
    otp = _generate_otp(user=user)
    send_otp_email_task.delay(user.id, otp.code)
    
    logger.info("User registered successfully", extra={"user_id": user.id, "username": user.username})

def login_user(*, identifier: str, password: str) -> tuple[User, str, str]:
    """
    Authenticate a user and issue tokens.

    Rules:
    - identifier can be username or email
    - password is validated
    """
    if "@" in identifier:
        user = User.objects.filter(email=identifier).first()
        if not user:
            logger.warning("Login failed - Invalid credentials", extra={"identifier": identifier})
            raise ValueError("Invalid login credentials")
        username = user.username
    else:
        username = identifier
    user = authenticate(username=username, password=password)

    if not user:
        logger.warning("Login failed - Invalid credentials", extra={"identifier": identifier})
        raise ValueError("Invalid login credentials or email not verified")

    logger.info("User login successful", extra={"username": user.username})
    access, refresh = _get_token_pair(user)
    return user, access, refresh

def logout_user(*, refresh: str) -> None:
    """
    Logout a user and blacklist their refresh token.

    Rules:
    - user is authenticated
    - refresh token is blacklisted
    """
    try:
        token = RefreshToken(refresh)
        token.blacklist()
    except TokenError:
        logger.error("Logout failed - invalid or expired token", exc_info=True)
        raise ValueError("Invalid or expired Token")
    
    logger.info("User logout successful")