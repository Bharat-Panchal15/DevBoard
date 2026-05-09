import pytest
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from users.models import OTPCode
from tests.factories import UserFactory

@pytest.mark.django_db
class TestUserModel:
    def test_str_returns_username(self):
        user = UserFactory()
        assert str(user) == user.username
    
    def test_email_must_be_unique(self):
        UserFactory(email="same@test.com")
        with pytest.raises(IntegrityError):
            UserFactory(email="same@test.com")

@pytest.mark.django_db
class TestOTPCodeModel:
    def test_otp_str_returns_correct_string(self):
        user = UserFactory()
        otp = OTPCode.objects.create(user=user, code="123456")

        assert str(otp) == f"OTP for {user.username}"

    def test_otp_is_expired_returns_false_for_fresh_otp(self):
        user = UserFactory()
        otp = OTPCode.objects.create(user=user, code="123456")

        assert otp.is_expired() == False

    def test_otp_is_expired_returns_true_for_expired_otp(self):
        user = UserFactory()
        otp = OTPCode.objects.create(user=user, code="123456")

        future_value = timezone.now() + timedelta(minutes=11)
        with patch("users.models.timezone.now", return_value=future_value):
            assert otp.is_expired() == True

    def test_otp_deleted_when_user_deleted(self):
        user = UserFactory()
        otp = OTPCode.objects.create(user=user, code="123456")
        otp_id = otp.id
        user.delete()

        assert not OTPCode.objects.filter(id=otp_id).exists()

    def test_one_user_can_have_only_one_otp(self):
        from django.db import IntegrityError
        user = UserFactory()
        otp = OTPCode.objects.create(user=user, code="123456")

        with pytest.raises(IntegrityError):
            OTPCode.objects.create(user=user, code="112233")