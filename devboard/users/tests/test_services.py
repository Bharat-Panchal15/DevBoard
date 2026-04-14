import pytest
from users.services import register_user, login_user, logout_user
from tests.factories import UserFactory
from rest_framework_simplejwt.tokens import RefreshToken

@pytest.mark.django_db
class TestRegisterServices:
    def test_create_user(self):
        user, _, __ = register_user(data={
            "username": "testuser",
            "email": "user@test.com",
            "password": "password123"
        })

        assert user.id is not None
        assert user.username == "testuser"

    def test_password_is_hashed(self):
        user, _, __ = register_user(data={
            "username": "testuser",
            "email": "user@test.com",
            "password": "password123"
        })

        assert user.password != "password123"
        assert user.check_password("password123")

    def test_returns_tokens(self):
        _, access, refresh = register_user(data={
            "username": "testuser",
            "email": "user@test.com",
            "password": "password123"
        })

        assert access is not None
        assert refresh is not None
    
    def test_duplicate_email_raises_error(self):
        UserFactory(email="user@test.com")
        with pytest.raises(ValueError):
            register_user(data={
                "username": "testuser",
                "email": "user@test.com",
                "password": "password123"
            })

@pytest.mark.django_db
class TestLoginService:
    def test_login_with_username(self, user):
        result_user, access, refresh = login_user(
            identifier=user.username,
            password="password123"
        )

        assert result_user == user
        assert access is not None
        assert refresh is not None

    def test_login_with_email(self, user):
        result_user, access, refresh = login_user(
            identifier=user.email,
            password="password123"
        )

        assert result_user == user
        assert access is not None
        assert refresh is not None

    def test_invalid_credentials_raises_error(self, user):
        with pytest.raises(ValueError):
            login_user(identifier=user.username, password="wrongpassword")

    def test_nonexistent_user_raises_error(self):
        with pytest.raises(ValueError):
            login_user(identifier="admin@test.com", password="password123")

@pytest.mark.django_db
class TestLogoutService:
    def test_valid_token_is_blacklisted(self, user):
        refresh = str(RefreshToken.for_user(user))

        # Should not raise error
        logout_user(refresh=refresh)

    def test_invalid_token_raises_error(self):
        with pytest.raises(ValueError):
            logout_user(refresh="invalidtoken")