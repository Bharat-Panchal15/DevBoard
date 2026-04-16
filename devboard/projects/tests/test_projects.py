import pytest
from tests.factories import UserFactory, ProjectFactory
from rest_framework.test import APIClient

@pytest.mark.django_db
class TestProjectListCreate:
    url = "/api/v1/projects/"

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.url)

        assert response.status_code == 401
    
    def test_returns_only_user_projects(self, auth_client, project):
        response = auth_client.get(self.url)
        ids = [proj["id"] for proj in response.data["results"]]

        assert response.status_code == 200
        assert project.id in ids
        assert len(ids) == 1

    def test_create_returns_201(self, auth_client):
        response = auth_client.post(self.url, {"name": "Test Project"})

        assert response.status_code == 201

@pytest.mark.django_db
class TestProjectDetail:
    def url(self, id):
        return f"/api/v1/projects/{id}/"
    
    def test_members_can_retrieve(self, auth_client, project):
        response = auth_client.get(self.url(project.id))

        assert response.status_code == 200

    def test_non_members_gets_404(self, auth_client):
        other_project = ProjectFactory()
        response = auth_client.get(self.url(other_project.id))

        assert response.status_code == 404

    def test_owner_can_patch(self, auth_client, project):
        response = auth_client.patch(self.url(project.id), {"description": "Updated"})

        assert response.status_code == 200
    
    def test_non_owner_cannot_patch(self, auth_client, project):
        member = UserFactory()
        project.members.add(member)
        client = APIClient()
        client.force_authenticate(user=member)
        response = client.patch(self.url(project.id), {"name": "Hacked Project"})

        assert response.status_code == 403

    def test_owner_can_delete(self, auth_client, project):
        response = auth_client.delete(self.url(project.id))

        assert response.status_code == 204

    def test_non_owner_cannot_delete(self, auth_client, project):
        member = UserFactory()
        project.members.add(member)
        client = APIClient()
        client.force_authenticate(user=member)
        response = client.delete(self.url(project.id))

        assert response.status_code == 403