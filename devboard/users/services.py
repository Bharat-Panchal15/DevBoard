from typing import Dict, Any
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from users.models import User

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

    password = data.pop("password")
    user = User.objects.create_user(**data, password=password)
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
            raise ValueError("Invalid login credentials")
        username = user.username
    else:
        username = identifier
    user = authenticate(username=username, password=password)

    if not user:
        raise ValueError("Invalid login credentials")

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
        raise ValueError("Invalid or expired Token")