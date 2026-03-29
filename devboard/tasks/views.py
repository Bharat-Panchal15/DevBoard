from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from tasks.serializers import TaskSerializer
from tasks.models import Task
from tasks.permissions import IsMember
from tasks.services import create_task, update_task, delete_task, assign_task, change_status
from projects.models import Project

class TaskListCreateView(ListCreateAPIView):
    """
    Task list & creation endpoint (within a project).

    Methods:
    - GET  /api/projects/{id}/tasks/   -> List all tasks for a project
    - POST /api/projects/{id}/tasks/   -> Create a new task in the project

    Permission:
    - Only project members can access

    GET Response:
    [
        {
            "id": 1,
            "title": "Setup backend",
            "description": "Initialize Django project",
            "project": 1,
            "assigned_to": 2,
            "status": "TODO",
            "due_date": "2026-03-25",
            "created_at": "2026-03-20T07:47:15Z"
        }
    ]

    POST Request:
    {
        "title": "Setup backend",
        "description": "Initialize Django project",
        "assigned_to": 2,
        "status": "TODO",
        "due_date": "2026-03-25"
    }

    POST Response:
    {
        "id": 1,
        "title": "Setup backend",
        "description": "Initialize Django project",
        "project": 1,
        "assigned_to": 2,
        "status": "TODO",
        "due_date": "2026-03-25",
        "created_at": "2026-03-20T07:47:15Z"
    }

    Validation:
    - assigned_to must be a project member
    - status must be one of: TODO, IN_PROGRESS, DONE

    Notes:
    - Project is taken from URL, not request body
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_project(self):
        """Fetch project and ensure user is a member"""
        if not hasattr(self, "_project"):
            project = get_object_or_404(Project, pk=self.kwargs["id"])

            if not project.members.filter(id=self.request.user.id).exists():
                raise PermissionDenied("You are not a member of this project")

            self._project = project

        return self._project
    
    def get_queryset(self):
        """Return task only for this project"""
        return Task.objects.filter(project= self.get_project())
    
    def get_serializer_context(self):
        """Pass project to serializer"""
        context = super().get_serializer_context()
        context["project"] = self.get_project()
        return context
    
    def perform_create(self, serializer):
        try:
            task = create_task(
                user=self.request.user,
                project=self.get_project(),
                data=serializer.validated_data
            )
        except Exception as err:
            raise ValidationError({"detail": str(err)})
        
        serializer.instance = task

class TaskDetailView(RetrieveUpdateDestroyAPIView):
    """
    Task detail endpoint.

    Methods:
    - GET    /api/tasks/{id}/     -> Retrieve task details
    - PUT    /api/tasks/{id}/     -> Update entire task
    - PATCH  /api/tasks/{id}/     -> Partial update
    - DELETE /api/tasks/{id}/     -> Delete task

    Permission:
    - Only project members can access
    - Enforced using IsMember permission

    GET Response:
    {
        "id": 1,
        "title": "Setup backend",
        "description": "Initialize Django project",
        "project": 1,
        "assigned_to": 2,
        "status": "TODO",
        "due_date": "2026-03-25",
        "created_at": "2026-03-20T07:47:15Z"
    }

    PATCH / PUT Examples:

    1. Update status:
    {
        "status": "DONE"
    }

    2. Assign task:
    {
        "assigned_to": 2
    }

    3. Unassign task:
    {
        "assigned_to": null
    }

    4. Update title/description:
    {
        "title": "Updated title",
        "description": "Updated description",
        "due_date": "2026-04-01"
    }

    DELETE Response:
    - 204 No Content

    Validation:
    - assigned_to must be a project member
    - status must be one of: TODO, IN_PROGRESS, DONE

    Notes:
    - Task must belong to a project where user is a member
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsMember]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return Task.objects.filter(project__members=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["project"] = self.get_object().project
        return context
    
    def perform_update(self, serializer):
        task = serializer.instance
        data = serializer.validated_data

        try:
            if "assigned_to" in data:
                assign_task(
                    user=self.request.user,
                    project=task.project,
                    task=task,
                    assignee=data["assigned_to"]
                )
            
            if "status" in data:
                change_status(
                    user=self.request.user,
                    project=task.project,
                    task=task,
                    status=data["status"]
                )

            update_fields = {key: value for key, value in data.items() if key not in ["assigned_to", "status"]}

            if update_fields:
                update_task(
                    user=self.request.user,
                    project=task.project,
                    task=task,
                    data=update_fields
                )
        except ValueError as err:
            raise ValidationError({"detail": str(err)})
        serializer.instance = task

    def perform_destroy(self, task):
        delete_task(
            user=self.request.user,
            project=task.project,
            task=task
        )