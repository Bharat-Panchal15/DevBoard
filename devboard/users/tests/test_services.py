import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from users.models import OTPCode
from users.services import register_user, login_user, logout_user, verify_otp, resend_otp
from tests.factories import UserFactory
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@pytest.mark.django_db
@patch("users.services.send_otp_email_task")
class TestRegisterService:
    def test_create_user(self, mock_task):
        register_user(data={
            "username": "testuser",
            "email": "user@test.com",
            "password": "password123"
        })
        user = User.objects.get(email="user@test.com")

        assert user.id is not None
        assert user.username == "testuser"

    def test_password_is_hashed(self, mock_task):
        register_user(data={
            "username": "testuser",
            "email": "user@test.com",
            "password": "password123"
        })
        user = User.objects.get(email="user@test.com")

        assert user.password != "password123"
        assert user.check_password("password123")
    
    def test_user_is_inactive_after_register(self, mock_task):
        register_user(data={
            "username": "testuser",
            "email": "user@test.com",
            "password": "password123"
        })
        user = User.objects.get(email="user@test.com")

        assert user.is_active == False
    
    def test_otp_generated_after_register(self, mock_task):
        register_user(data={
            "username": "testuser",
            "email": "user@test.com",
            "password": "password123"
        })
        user = User.objects.get(email="user@test.com")

        assert OTPCode.objects.filter(user=user).exists()
    
    def test_celery_task_fired_after_register(self, mock_task):
        register_user(data={
            "username": "testuser",
            "email": "user@test.com",
            "password": "password123"
        })
        user = User.objects.get(email="user@test.com")
        
        mock_task.delay.assert_called_once()
    
    def test_duplicate_email_raises_error(self, mock_task):
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
    
    def test_unverified_user_raises_error(self):
        unverified_user = UserFactory(is_active=False)

        with pytest.raises(ValueError):
            login_user(identifier=unverified_user.username, password="password123")

@pytest.mark.django_db
class TestLogoutService:
    def test_valid_token_is_blacklisted(self, user):
        refresh = str(RefreshToken.for_user(user))

        # Should not raise error
        logout_user(refresh=refresh)

    def test_invalid_token_raises_error(self):
        with pytest.raises(ValueError):
            logout_user(refresh="invalidtoken")

@pytest.mark.django_db
class TestVerifyOTPService:
    def test_verify_otp_activates_user(self):
        user = UserFactory(is_active=False)
        otp = OTPCode.objects.create(user=user, code="123456")

        with patch("users.services.send_welcome_email_task"):
            verify_otp(email=user.email, code="123456")
        
        user.refresh_from_db()
        assert user.is_active == True

    def test_verify_otp_returns_tokens(self):
        user = UserFactory(is_active=False)
        otp = OTPCode.objects.create(user=user, code="123456")

        with patch("users.services.send_welcome_email_task"):
            _, access, refresh = verify_otp(email=user.email, code="123456")
        
        assert access is not None
        assert refresh is not None

    def test_verify_otp_deletes_otp(self):
        user = UserFactory(is_active=False)
        otp = OTPCode.objects.create(user=user, code="123456")

        with patch("users.services.send_welcome_email_task"):
            verify_otp(email=user.email, code="123456")
        
        assert not OTPCode.objects.filter(user=user).exists()

    def test_expired_otp_raises_error(self):
        user = UserFactory(is_active=False)
        otp = OTPCode.objects.create(user=user, code="123456")

        future_time = timezone.now() + timedelta(minutes=11)
        with patch("users.models.timezone.now", return_value=future_time):
            with pytest.raises(ValueError):
                verify_otp(email=user.email, code="123456")

    def test_wrong_code_raises_error(self):
        user = UserFactory(is_active=False)
        otp = OTPCode.objects.create(user=user, code="123456")

        with pytest.raises(ValueError):
            verify_otp(email=user.email, code="654321")

    def test_invalid_email_raises_error(self):
        with pytest.raises(ValueError):
            verify_otp(email="wrong@test.com", code="123456")

@pytest.mark.django_db
class TestResendOTPService:
    def test_resend_generated_new_otp(self):
        user = UserFactory(is_active=False)
        OTPCode.objects.create(user=user, code="123456")

        with patch("users.services.send_otp_email_task"):
            resend_otp(email=user.email)
        
        otp = OTPCode.objects.get(user=user)

        assert otp.code != "123456"

    def test_resend_deletes_old_otp(self):
        user = UserFactory(is_active=False)
        old_otp = OTPCode.objects.create(user=user, code="123456")
        
        with patch("users.services.send_otp_email_task"):
            resend_otp(email=user.email)
        
        assert not OTPCode.objects.filter(id=old_otp.id).exists()

    def test_resend_already_verified_raises_error(self):
        user = UserFactory()

        with pytest.raises(ValueError):
            resend_otp(email=user.email)

    def test_resend_invalid_email_raises_error(self):
        with pytest.raises(ValueError):
            resend_otp(email="wrong@test.com")
    
    @patch("users.services.send_otp_email_task")
    def test_resend_celery_task_fired(self, mock_task):
        user = UserFactory(is_active=False)
        OTPCode.objects.create(user=user, code="123456")

        resend_otp(email=user.email)

        mock_task.delay.assert_called_once()