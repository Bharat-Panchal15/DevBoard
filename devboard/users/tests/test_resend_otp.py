import pytest
from unittest.mock import patch
from tests.factories import UserFactory

@pytest.mark.django_db
class TestResendOTPView:
    url = "/api/v1/otp/resend/"

    def test_valid_email_returns_200(self, api_client):
        user = UserFactory(is_active=False)

        with patch("users.services.send_otp_email_task"):
            response = api_client.post(self.url, {
                "email": user.email
            })

        assert response.status_code == 200

    def test_already_verified_returns_400(self, api_client):
        user = UserFactory()

        response = api_client.post(self.url, {
            "email": user.email
        })
        
        assert response.status_code == 400

    def test_invalid_email_returns_400(self, api_client):
        response = api_client.post(self.url, {
            "email": "wrong@test.com"
        })
        
        assert response.status_code == 400