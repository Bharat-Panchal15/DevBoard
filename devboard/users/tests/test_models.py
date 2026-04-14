import pytest
from django.db import IntegrityError
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