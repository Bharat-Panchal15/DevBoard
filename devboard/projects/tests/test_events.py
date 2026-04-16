import pytest
from services.events import create_event
from tests.factories import ProjectFactory

@pytest.mark.django_db
class TestEventListView:
    def url(self, id):
        return f"/api/v1/projects/{id}/events/"
    
    def test_unauthenticated_returns_401(self, api_client, project):
        response = api_client.get(self.url(project.id))

        assert response.status_code == 401
    
    def test_member_can_list_events(self, auth_client, project):
        response = auth_client.get(self.url(project.id))

        assert response.status_code == 200

    def test_non_member_gets_404(self, auth_client):
        other_project = ProjectFactory()
        response = auth_client.get(self.url(other_project.id))

        assert response.status_code == 404

    def test_returns_events_for_project(self, auth_client, user, project):
        create_event(actor=user, action="PROJECT_CREATED", project=project)
        response = auth_client.get(self.url(project.id))

        assert response.data["count"] >= 1

    def test_events_ordered_newest_first(self, auth_client, user, project):
        create_event(actor=user, action="PROJECT_CREATED", project=project)
        create_event(actor=user, action="PROJECT_UPDATED", project=project)
        response = auth_client.get(self.url(project.id)).data["results"]
        
        assert response[0]["action"] == "PROJECT_UPDATED"