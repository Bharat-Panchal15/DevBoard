import pytest

@pytest.mark.django_db
class TestLoginView:
    url = "/api/v1/login/"

    def test_valid_username_returns_200(self, api_client, user):
        response = api_client.post(self.url, {
            "identifier": user.username,
            "password": "password123"
        })

        assert response.status_code == 200
    
    def test_valid_email_returns_200(self, api_client, user):
        response = api_client.post(self.url, {
            "identifier": user.email,
            "password": "password123"
        })

        assert response.status_code == 200
    
    def test_response_contains_tokens(self, api_client, user):
        response = api_client.post(self.url, {
            "identifier": user.username,
            "password": "password123"
        })

        assert "access" in response.data
        assert "refresh" in response.data

    def test_wrong_password_returns_400(self, api_client, user):
        response = api_client.post(self.url, {
            "identifier": user.username,
            "password": "wrongpassword"
        })

        assert response.status_code == 400

    def test_nonexistent_user_returns_400(self, api_client):
        response = api_client.post(self.url, {
            "identifier": "nonexistent",
            "password": "password123"
        })

        assert response.status_code == 400

    def test_authenticated_user_returns_403(self, auth_client, user):
        response = auth_client.post(self.url, {
            "identifier": user.username,
            "password": "password123"
        })

        assert response.status_code == 403