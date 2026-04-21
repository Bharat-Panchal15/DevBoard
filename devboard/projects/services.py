import logging
from typing import Dict, Any
from users.models import User
from projects.models import Project
from services.events import create_event

logger = logging.getLogger("api.projects")

def create_project(*, user: User, data: Dict[str,Any]) -> Project:
    """Create a new Project
    
    Rules:
    - owner becomes project owner
    - owner must be added to members
    - event must be created
    """

    # Create Project
    project = Project.objects.create(owner = user,**data)

    # Add owner to members
    project.members.add(user)

    # Create event
    create_event(actor=user, action="PROJECT_CREATED", project=project)
    logger.info("Project created", extra={"project_id": project.id, "user_id": user.id})
    
    return project

def update_project(*, user: User, project: Project, data: Dict[str, Any]) -> Project:
    """
    Update project fields.
    
    Rules:
    - owner owner can update
    - track field-level changes
    - create event only if something changed
    """
    
    changes: Dict[str, Dict[str, Any]] = {}

    for field in ["name", "description"]:
        old_value = getattr(project, field)
        new_value = data.get(field, old_value)

        if new_value != old_value:
            changes[field] = {
                "from": old_value if old_value else None,
                "to": new_value if new_value else None
            }
            setattr(project, field, new_value)
        
    if changes:
        project.save()

        create_event(
            actor=user,
            action="PROJECT_UPDATED",
            project=project,
            metadata={"fields": changes}
        )
        logger.info("Project updated", extra={"project_id": project.id, "user_id": user.id, "fields": list(changes.keys())})
    
    return project

def remove_project(*, user: User, project: Project) -> None:
    """
    Delete a project.

    Rules:
    - only owner can delete
    - no event required
    """
    project_id = project.id
    project.delete()
    logger.info("Project deleted", extra={"project_id":project_id, "user_id": user.id})

def add_member(*, user: User, project: Project, member: User) -> None:
    """
    Add a member to a project.

    Rules:
    - only owner can add members
    - member must not already exist
    - event must be created
    """
        
    if project.members.filter(id=member.id).exists():
        logger.warning("Add member failed - already a member", extra={"project_id": project.id, "user_id": user.id, "member_id": member.id})
        raise ValueError("User is already a member")
    
    project.members.add(member)

    create_event(
        actor=user,
        action="MEMBER_ADDED",
        project=project,
        target_user=member
    )
    logger.info("Member added", extra={"project_id": project.id, "user_id": user.id, "member_id": member.id})

def remove_member(*, user: User, project: Project, member: User) -> None:
    """
    Remove a member from project.

    Rules:
    - only owner can remove members
    - owner cannot be removed
    - member must exist in project
    - event must be created
    """
    
    if member == project.owner:
        logger.warning("Remove member failed - cannot remove owner", extra={"project_id": project.id, "user_id": user.id, "member_id": member.id})
        raise ValueError("Owner cannot be removed from the project")
    
    if not project.members.filter(id=member.id).exists():
        logger.warning("Remove member failed - not a member", extra={"project_id": project.id, "user_id": user.id, "member_id": member.id})
        raise ValueError("User is not a member of this project")
    
    project.members.remove(member)

    create_event(
        actor=user,
        action="MEMBER_REMOVED",
        project=project,
        target_user=member
    )
    logger.info("Member removed", extra={"project_id": project.id, "member_id": member.id, "user_id": user.id})