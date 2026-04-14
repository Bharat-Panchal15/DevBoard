import pytest
from rest_framework_simplejwt.tokens import RefreshToken

@pytest.mark.django_db
class TestLogoutView:
    url = "/api/v1/logout/"

    def test_valid_token_returns_204(self, auth_client, user):
        refresh = str(RefreshToken.for_user(user))
        response = auth_client.post(self.url, {"refresh": refresh})

        assert response.status_code == 204

    def test_invalid_token_returns_400(self, auth_client):
        response = auth_client.post(self.url, {"refresh": "invalidtoken"})

        assert response.status_code == 400

    def test_unauthenticated_request_returns_401(self, api_client, user):
        refresh = str(RefreshToken.for_user(user))
        response = api_client.post(self.url, {"refresh": refresh})

        assert response.status_code == 401