from typing import Optional, Dict, Any
from users.models import User
from projects.models import Project
from tasks.models import Task
from services.events import create_event


def create_task(*, user: User, project: Project, data: Dict[str, Any]) -> Task:
    """
    Create a new task.

    Rules:
    - user must be a project member.
    - assigned_to (if provided) must be a project member.
    - created_by is always user
    - event must be created
    """

    if not project.members.filter(id=user.id).exists():
        raise ValueError("User is not a member of this project")
    
    assigned_to: Optional[User] = data.get("assigned_to")

    if assigned_to and not project.members.filter(id=assigned_to.id).exists():
        raise ValueError("Assigned user must be a project member")
    
    task = Task.objects.create(
        project=project,
        created_by=user,
        **data
    )

    create_event(
        actor=user,
        action="TASK_CREATED",
        project=project,
        task=task
    )

    return task

def update_task(*, user: User, project: Project, task: Task, data: Dict[str, Any]) -> Task:
    """
    Update a task.

    Rules:
    - user must be a project member
    - track field-level changes
    - create event only if something changed
    """

    changes: Dict[str, Dict[str, Any]] = {}

    for field in ["title", "description", "due_date"]:
        old_value = getattr(task, field)
        new_value = data.get(field, old_value)

        if new_value != old_value:
            changes[field] = {
                "from": str(old_value) if old_value else None,
                "to": str(new_value) if new_value else None
            }

            setattr(task, field, new_value)
    
    if changes:
        task.save()

        create_event(
            actor=user,
            action="TASK_UPDATED",
            project=project,
            task=task,
            metadata={"fields": changes}
        )
    
    return task

def delete_task(*,user: User, project: Project, task: Task) -> None:
    """
    Delete a task.

    Rules:
    - user must be a project member
    - no event required
    """

    task.delete()

def assign_task(*, user: User, project: Project, task: Task, assignee: Optional[User]) -> Task:
    """
    Assign or unasign a task.

    Rules:
    - user must be a project member
    - assignee msut be a project member(if provided)
    - create event only if assignee changed
    """

    if assignee and project.members.filter(id=assignee.id).exists():
        raise ValueError("Assigned user must be a project member")
    
    old_assignee = task.assigned_to

    if old_assignee == assignee:
        return task
    
    task.assigned_to = assignee
    task.save()

    create_event(
        actor=user,
        action="TASK_ASSIGNED",
        project=project,
        task=task,
        target_user=assignee,
        metadata={
            "from": old_assignee.id if old_assignee else None,
            "to": assignee.id if assignee else None
        }
    )

    return task

def change_status(*, user: User, project: Project, task: Task, status: str) -> Task:
    """
    Change task status.

    Rules:
    - user must be a project member
    - status must be a valid choice
    - create event only if status changed
    """

    old_status = task.status

    if old_status == status:
        return task
    
    task.status = status
    task.save()

    create_event(
        actor=user,
        action="STATUS_UPDATED",
        project=project,
        task=task,
        metadata={
            "from": old_status,
            "to": status
        }
    )

    return task