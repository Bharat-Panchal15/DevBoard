import pytest
from rest_framework.test import APIClient
from tests.factories import UserFactory

@pytest.mark.django_db
class TestCommentListCreate:
    def url(self, task_id):
        return f"/api/v1/tasks/{task_id}/comments/"
    
    def test_unauthenticated_returns_401(self, api_client, task):
        response = api_client.get(self.url(task.id))

        assert response.status_code == 401

    def test_non_member_gets_403(self, task):
        outsider = UserFactory()
        client = APIClient()
        client.force_authenticate(user=outsider)
        response = client.get(self.url(task.id))

        assert response.status_code == 403
    
    def test_member_can_list_comments(self, auth_client, task):
        response = auth_client.get(self.url(task.id))

        assert response.status_code == 200
    
    def test_member_can_create_comments(self, auth_client, task):
        response = auth_client.post(self.url(task.id), {"content": "Test Comment!"})

        assert response.status_code == 201

    def test_empty_comment_returns_400(self, auth_client, task):
        response = auth_client.post(self.url(task.id), {"content": "   "})

        assert response.status_code == 400

@pytest.mark.django_db
class TestCommentDetail:
    def url(self, comment_id):
        return f"/api/v1/comments/{comment_id}/"
    
    def test_author_can_delete_comment(self, auth_client, comment):
        response = auth_client.delete(self.url(comment.id))

        assert response.status_code == 204

    def test_non_author_cannot_delete(self, comment):
        other_member = UserFactory()
        comment.task.project.members.add(other_member)
        client = APIClient()
        client.force_authenticate(user=other_member)
        response = client.delete(self.url(comment.id))

        assert response.status_code == 403

    def test_unauthenticated_returns_401(self, api_client, comment):
        response = api_client.delete(self.url(comment.id))

        assert response.status_code == 401