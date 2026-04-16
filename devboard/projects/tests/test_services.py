import pytest
from projects.models import Project, Event
from projects.services import create_project, update_project, remove_project, add_member, remove_member
from tests.factories import UserFactory, ProjectFactory

@pytest.mark.django_db
class TestCreateProject:
    def test_creates_project(self, user):
        project = create_project(user=user, data={"name": "Test Project", "description": ""})

        assert project.id is not None
        assert project.owner == user
    
    def test_owner_added_to_members(self, user):
        project = create_project(user=user, data={"name": "Test Project", "description": ""})

        assert project.members.filter(id=user.id).exists()
    
    def test_project_created_event_fired(self, user):
        project = create_project(user=user, data={"name": "Test Project", "description": ""})

        assert Event.objects.filter(project=project, action="PROJECT_CREATED").exists()

@pytest.mark.django_db
class TestUpdateProject:
    def test_updates_fields(self, user, project):
        update_project(user=user, project=project, data={"name": "New name"})
        project.refresh_from_db()

        assert project.name == "New name"
    
    def test_project_update_event_fired(self, user, project):
        update_project(user=user, project=project, data={"name": "New name"})

        assert Event.objects.filter(project=project, action="PROJECT_UPDATED").exists()
    
    def test_no_event_if_nothing_changed(self, user, project):
        update_project(user=user, project=project, data={"name": project.name})

        assert not Event.objects.filter(project=project, action="PROJECT_UPDATED").exists()

@pytest.mark.django_db
class TestRemoveProject:
    def test_deletes_project(self, user, project):
        remove_project(user=user, project=project)

        assert not Project.objects.filter(id=project.id).exists()

@pytest.mark.django_db
class TestAddMember:
    def test_adds_member(self, user, project):
        new_member = UserFactory()
        add_member(user=user, project=project, member=new_member)

        assert project.members.filter(id=new_member.id).exists()

    def test_member_added_event_fired(self, user, project):
        new_member = UserFactory()
        add_member(user=user, project=project, member=new_member)
        
        assert Event.objects.filter(project=project, action="MEMBER_ADDED", target_user=new_member).exists()

    def test_raises_error_if_already_member(self, user, project):
        new_member = UserFactory()
        add_member(user=user, project=project, member=new_member)

        with pytest.raises(ValueError):
            add_member(user=user, project=project, member=new_member)

@pytest.mark.django_db
class TestRemoveMember:
    def test_remove_member(self, user, project):
        member = UserFactory()
        project.members.add(member)
        remove_member(user=user, project=project, member=member)

        assert not project.members.filter(id=member.id).exists()

    def test_member_removed_event_is_fired(self, user, project):
        member = UserFactory()
        project.members.add(member)
        remove_member(user=user, project=project, member=member)
        
        assert Event.objects.filter(project=project, action="MEMBER_REMOVED", target_user=member).exists()

    def test_raises_error_if_not_a_member(self, user, project):
        outsider = UserFactory()
        with pytest.raises(ValueError):
            remove_member(user=user, project=project, member=outsider)

    def test_raises_error_if_removing_owner(self, user, project):
        with pytest.raises(ValueError):
            remove_member(user=user, project=project, member=user)