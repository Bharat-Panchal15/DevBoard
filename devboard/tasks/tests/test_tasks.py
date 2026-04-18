import pytest
from rest_framework.test import APIClient
from tests.factories import UserFactory, TaskFactory

@pytest.mark.django_db
class TestTaskListCreate:
    def url(self, project_id):
        return f"/api/v1/projects/{project_id}/tasks/"
    
    def test_unauthenticated_returns_401(self, api_client, project):
        response = api_client.get(self.url(project.id))

        assert response.status_code == 401
    
    def test_non_member_gets_403(self, project):
        outsider = UserFactory()
        client = APIClient()
        client.force_authenticate(user=outsider)
        response = client.get(self.url(project.id))

        assert response.status_code == 403

    def test_memer_can_list_tasks(self, auth_client, project):
        response = auth_client.get(self.url(project.id))

        assert response.status_code == 200
    
    def test_member_can_create_tasks(self, auth_client, project):
        response = auth_client.post(self.url(project.id), {"title": "Test Task"})

        assert response.status_code == 201

    def test_filter_by_status(self, auth_client, user, project):
        TaskFactory(project=project, created_by=user, status="TODO")
        TaskFactory(project=project, created_by=user, status="DONE")
        response = auth_client.get(self.url(project.id), {"status": "DONE"})
        results = response.data["results"]

        assert response.status_code == 200
        assert all(result_task["status"] == "DONE" for result_task in results)
        

    def test_filter_by_assigned_to_me(self, auth_client, user, project):
        TaskFactory(project=project, created_by=user, assigned_to=user)
        TaskFactory(project=project, created_by=user)
        response = auth_client.get(self.url(project.id), {"assigned_to": "me"})
        results = response.data["results"]

        assert response.status_code == 200
        assert all(result_task["assigned_to"] == user.id for result_task in results)


    def test_search_by_title(self, auth_client, user, project):
        TaskFactory(project=project, created_by=user, title="Fix the bug")
        TaskFactory(project=project, created_by=user, title="Write tests")
        response = auth_client.get(self.url(project.id), {"search": "bug"})
        results = response.data["results"]

        assert response.status_code == 200
        assert len(results) == 1
        assert results[0]["title"] == "Fix the bug"

@pytest.mark.django_db
class TestTaskDetail:
    def url(self, task_id):
        return f"/api/v1/tasks/{task_id}/"
    
    def test_member_can_retrieve_task(self, auth_client, task):
        response = auth_client.get(self.url(task.id))

        assert response.status_code == 200

    def test_non_member_gets_404(self, task):
        outsider = UserFactory()
        client = APIClient()
        client.force_authenticate(user=outsider)
        response = client.get(self.url(task.id))

        assert response.status_code == 404

    def test_member_can_update_task(self, auth_client, task):
        response = auth_client.patch(self.url(task.id), {"title": "Updated Title"})

        assert response.status_code == 200

    def test_member_can_delete_task(self, auth_client, task):
        response = auth_client.delete(self.url(task.id))

        assert response.status_code == 204

    def test_can_assign_task(self, auth_client, user, project, task):
        assignee = UserFactory()
        project.members.add(assignee)
        response = auth_client.patch(self.url(task.id), {"assigned_to": assignee.id})
        task.refresh_from_db()

        assert response.status_code == 200
        assert task.assigned_to == assignee        

    def test_can_change_status(self, auth_client, task):
        response = auth_client.patch(self.url(task.id), {"status": "IN_PROGRESS"})
        task.refresh_from_db()

        assert response.status_code == 200
        assert task.status == "IN_PROGRESS"