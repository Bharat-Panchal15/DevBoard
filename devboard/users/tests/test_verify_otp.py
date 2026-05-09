import pytest
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta
from tests.factories import UserFactory
from users.models import OTPCode

@pytest.mark.django_db
class TestVerifyOTPView:
    url = "/api/v1/otp/verify/"

    def test_valid_code_returns_200(self, api_client):
        user = UserFactory(is_active=False)
        OTPCode.objects.create(user=user, code="123456")

        with patch("users.services.send_welcome_email_task"):
            response = api_client.post(self.url, {
                "email": user.email,
                "code": "123456"
            })
        
        assert response.status_code == 200

    def test_invalid_code_returns_400(self, api_client):
        user = UserFactory(is_active=False)
        OTPCode.objects.create(user=user, code="123456")

        response = api_client.post(self.url, {
            "email": user.email,
            "code": "654321"
        })

        assert response.status_code == 400

    def test_expired_code_returns_400(self, api_client):
        user = UserFactory(is_active=False)
        OTPCode.objects.create(user=user, code="123456")

        future_time = timezone.now() + timedelta(minutes=11)
        with patch("users.models.timezone.now", return_value=future_time):
            response = api_client.post(self.url, {
                "email": user.email,
                "code": "123456"
            })
        
        assert response.status_code == 400