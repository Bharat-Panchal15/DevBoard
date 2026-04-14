import pytest
from tests.factories import TaskFactory, CommentFactory

@pytest.fixture
def task(project, user):
    return TaskFactory(project=project, created_by=user)

@pytest.fixture
def comment(task, user):
    return CommentFactory(task=task, author=user)