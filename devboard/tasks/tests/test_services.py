import pytest
from tasks.models import Task, Comment
from projects.models import Event
from tests.factories import UserFactory, TaskFactory, CommentFactory
from tasks.services import create_task, update_task, delete_task, assign_task, change_status, create_comment, delete_comment

@pytest.mark.django_db
class TestCreateTask:
    def test_creates_task(self, user, project):
        task = create_task(user=user, project=project, data={"title": "Test Task"})

        assert task.id is not None
        assert task.title == "Test Task"
        assert task.created_by == user
        assert task.project == project

    def test_task_created_event_fired(self, user, project):
        task = create_task(user=user, project=project, data={"title": "Test Task"})
        
        assert Event.objects.filter(project=project, task=task, action="TASK_CREATED").exists()

    def test_raises_error_if_assigned_to_non_member(self, user, project):
        outsider = UserFactory()
        with pytest.raises(ValueError):
            task = create_task(user=user, project=project, data={"title": "Test Task", "assigned_to": outsider})
    
    def test_task_created_event_is_fired(self, user, project):
        task = create_task(user=user, project=project, data={"title": "Test Task"})

        assert Event.objects.filter(project=project, task=task, action="TASK_CREATED").exists()

@pytest.mark.django_db
class TestUpdateTask:
    def test_updates_fields(self, user, project, task):
        update_task(user=user, project=project, task=task, data={"title": "Updated Title"})
        task.refresh_from_db()

        assert task.title == "Updated Title"
    
    def test_task_updated_event_fired(self, user, project, task):
        update_task(user=user, project=project, task=task, data={"title": "Updated Title"})

        assert Event.objects.filter(project=project, task=task, action="TASK_UPDATED").exists()
    
    def test_no_event_if_nothing_changed(self, user, project, task):
        update_task(user=user, project=project, task=task, data={"title": task.title})

        assert not Event.objects.filter(project=project, task=task, action="TASK_UPDATED").exists()
    
    def test_metadata_contains_changed_fields(self, user, project, task):
        update_task(user=user, project=project, task=task, data={"title": "Updated Title"})
        event = Event.objects.get(project=project, task=task, action="TASK_UPDATED")

        assert "title" in event.metadata["fields"]

@pytest.mark.django_db
class TestTaskDelete:
    def test_deletes_task(self, user, project, task):
        task_id = task.id
        delete_task(user=user, project=project, task=task)

        assert not Task.objects.filter(id=task_id).exists()

@pytest.mark.django_db
class TestAssignTask:
    def test_assigns_task(self, user, project, task):
        assignee = UserFactory()
        project.members.add(assignee)
        assign_task(user=user, project=project, task=task, assignee=assignee)
        task.refresh_from_db()

        assert task.assigned_to == assignee

    def test_unassigns_task(self, user, project, task):
        assignee = UserFactory()
        project.members.add(assignee)
        task.assigned_to = assignee
        task.save()

        assign_task(user=user, project=project, task=task, assignee=None)
        task.refresh_from_db()

        assert task.assigned_to is None

    def test_non_member_assigneee_raises_error(self, user, project, task):
        outsider = UserFactory()

        with pytest.raises(ValueError):
            assign_task(user=user, project=project, task=task, assignee=outsider)

    def test_no_event_if_assignee_unchanged(self, user, project, task):
        assign_task(user=user, project=project, task=task, assignee=task.assigned_to)

        assert not Event.objects.filter(project=project, task=task, action="TASK_ASSIGNED").exists()

    def test_task_assigned_event_fired(self, user, project, task):
        assignee = UserFactory()
        project.members.add(assignee)
        assign_task(user=user, project=project, task=task, assignee=assignee)
        
        assert Event.objects.filter(project=project, task=task, action="TASK_ASSIGNED").exists()

@pytest.mark.django_db
class TestChangeStatus:
    def test_changes_status(self, user, project, task):
        change_status(user=user, project=project, task=task, status="IN_PROGRESS")
        task.refresh_from_db()

        assert task.status == "IN_PROGRESS"

    def test_no_event_if_status_unchanged(self, user, project, task):
        change_status(user=user, project=project, task=task, status=task.status)

        assert not Event.objects.filter(project=project, task=task, action="STATUS_UPDATED").exists()

    def test_status_updated_event_fired(self, user, project, task):
        change_status(user=user, project=project, task=task, status="DONE")

        assert Event.objects.filter(project=project, task=task, action="STATUS_UPDATED").exists()

@pytest.mark.django_db
class TestCreateComment:
    def test_creates_comment(self, user, task):
        comment = create_comment(user=user, task=task, data={"content": "Test Comment!"})

        assert comment.id is not None
        assert comment.content == "Test Comment!"
        assert comment.author == user
        assert comment.task == task

    def test_comment_added_event_fired(self, user, task, project):
        create_comment(user=user, task=task, data={"content": "Nice Work!"})

        assert Event.objects.filter(project=project, task=task, action="COMMENT_ADDED").exists()

@pytest.mark.django_db
class TestDeleteComment:
    def test_deletes_comment(self, user, task, comment):
        delete_comment(user=user, task=task, comment=comment)

        assert not Comment.objects.filter(id=comment.id).exists()