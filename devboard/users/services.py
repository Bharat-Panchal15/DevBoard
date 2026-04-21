import logging
from typing import Dict, Any
from django.contrib.auth import authenticate
from django.db import IntegrityError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from users.models import User

logger = logging.getLogger("api.users")

def _get_token_pair(user: User) -> tuple[str, str]:
    """
    Helper: Build token pair for a user
    """
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    return str(access), str(refresh)

def register_user(*, data: Dict[str, Any]) -> tuple[User, str, str]:
    """
    Create a new user account.

    Rules:
    - email must be unique
    - password is hashed before storage
    """
    try:
        password = data.pop("password")
        user = User.objects.create_user(**data, password=password)
    except IntegrityError:
        logger.warning("Registration failed - duplicate email", extra={"email": data.get("email")})
        raise ValueError("A user with this email already exists")
    
    logger.info("User registered successfully", extra={"user_id": user.id, "username": user.username})
    access, refresh = _get_token_pair(user)
    return user, access, refresh

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
        raise ValueError("Invalid login credentials")

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