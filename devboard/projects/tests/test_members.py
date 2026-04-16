import pytest
from rest_framework.test import APIClient
from tests.factories import UserFactory, ProjectFactory

@pytest.mark.django_db
class TestProjectMember:
    def members_url(self, id):
        return f"/api/v1/projects/{id}/members/"
    
    def remove_url(self, project_id, member_id):
        return f"/api/v1/projects/{project_id}/members/{member_id}/"
    
    def test_member_can_list_members(self, auth_client, project):
        response = auth_client.get(self.members_url(project.id))

        assert response.status_code == 200

    def test_non_member_gets_404(self, auth_client):
        other_project = ProjectFactory()
        response = auth_client.get(self.members_url(other_project.id))

        assert response.status_code == 404

    def test_owner_can_add_member(self, auth_client, project):
        new_user = UserFactory()
        response = auth_client.post(self.members_url(project.id), {"user_id": new_user.id})

        assert response.status_code == 201

    def test_non_owner_cannot_add_member(self, project):
        member = UserFactory()
        project.members.add(member)
        client = APIClient()
        client.force_authenticate(user=member)
        new_user = UserFactory()
        response = client.post(self.members_url(project.id), {"user_id": new_user.id})

        assert response.status_code == 403

    def test_add_existing_members_return_400(self, auth_client, project):
        member = UserFactory()
        project.members.add(member)
        response = auth_client.post(self.members_url(project.id), {"user_id": member.id})

        assert response.status_code == 400
        
    def test_add_nonexisting_user_returns_400(self, auth_client, project):
        response = auth_client.post(self.members_url(project.id), {"user_id": 9999})

        assert response.status_code == 400

    def test_owner_can_remove_member(self, auth_client, project):
        member = UserFactory()
        project.members.add(member)
        response = auth_client.delete(self.remove_url(project.id, member.id))

        assert response.status_code == 204

    def test_cannot_remove_owner(self, auth_client, project, user):
        response = auth_client.delete(self.remove_url(project.id, user.id))

        assert response.status_code == 400

    def test_cannot_remove_non_member(self, auth_client, project):
        outsider = UserFactory()
        response = auth_client.delete(self.remove_url(project.id, outsider.id))

        assert response.status_code == 400