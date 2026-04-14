import pytest
from tests.factories import UserFactory

@pytest.fixture
def member(db):
    return UserFactory()