import pytest
from unittest.mock import patch

@pytest.mark.django_db
@patch("users.services.send_otp_email_task")
class TestRegisterView:
    url = "/api/v1/register/"

    def test_valid_data_returns_201(self, mock_task, api_client, user_data):
        response = api_client.post(self.url, user_data)

        assert response.status_code == 201

    def test_response_contains_detail_message(self, mock_task, api_client, user_data):
        response = api_client.post(self.url, user_data)

        assert "detail" in response.data    

    def test_duplicate_email_return_400(self, mock_task, api_client, user_data, user):
        user_data["email"] = user.email
        response = api_client.post(self.url, user_data)

        assert response.status_code == 400

    def test_username_with_at_symbol_returns_400(self, mock_task, api_client, user_data):
        user_data["username"] = "test@user"
        response = api_client.post(self.url, user_data)

        assert response.status_code == 400

    def test_missing_fields_returns_400(self, mock_task, api_client):
        response = api_client.post(self.url, {})

        assert response.status_code == 400

    def test_authenticated_user_returns_403(self, mock_task, auth_client, user_data):
        response = auth_client.post(self.url, user_data)

        assert response.status_code == 403