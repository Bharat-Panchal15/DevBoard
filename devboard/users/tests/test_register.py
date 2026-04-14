import pytest

@pytest.mark.django_db
class TestRegisterView:
    url = "/api/v1/register/"

    def test_valid_data_returns_201(self, api_client, user_data):
        response = api_client.post(self.url, user_data)

        assert response.status_code == 201

    def test_response_contains_tokens(self, api_client, user_data):
        response = api_client.post(self.url, user_data)

        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data

    def test_duplicate_email_return_400(self, api_client, user_data, user):
        user_data["email"] = user.email
        response = api_client.post(self.url, user_data)

        assert response.status_code == 400

    def test_username_with_at_symbol_returns_400(self, api_client, user_data):
        user_data["username"] = "test@user"
        response = api_client.post(self.url, user_data)

        assert response.status_code == 400

    def test_missing_fields_returns_400(self, api_client):
        response = api_client.post(self.url, {})

        assert response.status_code == 400

    def test_authenticated_user_returns_403(self, auth_client, user_data):
        response = auth_client.post(self.url, user_data)

        assert response.status_code == 403