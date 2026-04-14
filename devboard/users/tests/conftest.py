import pytest

@pytest.fixture
def user_data():
    return {
        "username": "testuser",
        "email": "user@test.com",
        "password": "password123"
    }