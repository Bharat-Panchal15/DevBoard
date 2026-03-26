from typing import Optional, Dict, Any
from users.models import User
from projects.models import Project, Event
from tasks.models import Task

def create_event(
        *,
        actor: User,
        action: str,
        project: Project,
        task: Optional[Task] = None,
        target_user: Optional[User] = None,
        metadata: Optional[Dict[str, Any]] = None
) -> Event:
    """
    Centralized event creation.
    
    Rules enforced:
    - task must belong to project (if provided)
    - metadata must be dict or None
    """

    # Validate action
    if action not in Event.ActionChoices.values:
        raise ValueError("Invalid action type")
    
    # Validate actor belongs to project
    if not project.members.filter(id=actor.id).exists():
        raise ValueError("Actor must be a part of the project")
    
    # Validate task belongs to project
    if task and task.project_id != project.id:
        raise ValueError("Task does not belong to the given project")
    
    # Validate metadata
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("Metadata must be a dictionary")
    
    return Event.objects.create(
        actor=actor,
        action=action,
        project=project,
        task=task,
        target_user=target_user,
        metadata=metadata
    )