import pytest
from tests.factories import UserFactory, ProjectFactory, TaskFactory
from projects.models import Project, Event
from services.events import create_event

@pytest.mark.django_db
class TestProjectModel:
    def test_str_returns_name(self):
        project = ProjectFactory()
        
        assert str(project) == project.name
    
    def test_owner_cascade_deletes_project(self):
        project = ProjectFactory()
        project.owner.delete()

        assert not Project.objects.filter(id=project.id).exists()

@pytest.mark.django_db
class TestEventModel:
    def test_str_returns_actor_and_action(self, user, project):
        event = create_event(actor=user, action="PROJECT_CREATED", project=project)

        assert str(event) == f"{user} - PROJECT_CREATED"
    
    def test_task_must_belong_to_project(self, user, project):
        other_project = ProjectFactory(owner=user, members=[])
        task = TaskFactory(project=other_project, created_by=user)

        with pytest.raises(ValueError):
            create_event(actor=user, action="TASK_CREATED", project=project, task=task)