import pytest
from tests.factories import UserFactory, ProjectFactory, TaskFactory, CommentFactory
from tasks.models import Task, Comment

@pytest.mark.django_db
class TestTaskModel:
    def test_str_returns_title(self, task):
        assert str(task) == task.title

    def test_project_cascade_deletes_task(self, task):
        task_id = task.id
        task.project.delete()

        assert not Task.objects.filter(id=task_id).exists()

@pytest.mark.django_db
class TestCommentModel:
    def test_str_returns_author_and_task(self, comment):
        assert str(comment) == f"{comment.author} - {comment.task}"
    
    def test_task_cascade_deletes_comments(self, comment):
        comment_id = comment.id
        comment.task.delete()

        assert not Comment.objects.filter(id=comment_id).exists()