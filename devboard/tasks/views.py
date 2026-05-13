from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from tasks.serializers import TaskSerializer, CommentSerializer
from tasks.models import Task, Comment
from tasks.permissions import IsMember, IsAuthor
from tasks.services import create_task, update_task, delete_task, assign_task, change_status, create_comment, delete_comment
from tasks.throttles import TaskRateThrottle, CommentRateThrottle
from projects.models import Project

@extend_schema_view(
    get=extend_schema(
        tags=["Tasks"],
        summary="List all tasks for a project",
        description="Returns a paginated list of all tasks for a project. Supports filtering by status, assigned_to, search by title, and ordering. Only accessible to project members."
    ),
    post=extend_schema(
        tags=["Tasks"],
        summary="Create a new task",
        description="Creates a new task in the project. The authenticated user is automatically set as created_by. assigned_to must be a project member."
    ),
)
class TaskListCreateView(ListCreateAPIView):
    """
    Task list & creation endpoint.

    Methods:
    - GET  /api/v1/projects/{id}/tasks/   -> List all tasks for a project
    - POST /api/v1/projects/{id}/tasks/   -> Create a new task in the project

    Permission:
    - Project members only

    GET Response (200):
    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 1,
                "title": "Fix the bug",
                "description": "Investigate and fix the login bug",
                "project": 1,
                "assigned_to": 2,
                "created_by": "user1",
                "status": "TODO",
                "due_date": "2026-04-01",
                "created_at": "2026-03-20T07:47:15Z"
            }
        ]
    }

    POST Request:
    {
        "title": "Fix the bug",
        "description": "Investigate and fix the login bug",
        "assigned_to": 2,
        "status": "TODO",
        "due_date": "2026-04-01"
    }

    POST Response (201):
    {
        "id": 1,
        "title": "Fix the bug",
        "description": "Investigate and fix the login bug",
        "project": 1,
        "assigned_to": 2,
        "created_by": "user1",
        "status": "TODO",
        "due_date": "2026-04-01",
        "created_at": "2026-03-20T07:47:15Z"
    }

    Filtering / Search / Ordering:
    - ?status=TODO              -> Filter by status (TODO, IN_PROGRESS, DONE)
    - ?assigned_to=me           -> Filter tasks assigned to the authenticated user
    - ?assigned_to={user_id}    -> Filter tasks assigned to a specific user
    - ?search=keyword           -> Search by title
    - ?ordering=due_date        -> Order by due_date or created_at (prefix - for descending)

    Validation:
    - assigned_to must be a project member
    - status must be one of: TODO, IN_PROGRESS, DONE

    Notes:
    - Non-members receive 403.
    - Project is taken from the URL, not the request body.
    - created_by is automatically set to the authenticated user.
    - Results are paginated (default page size: 20).
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    filterset_fields = ["status"]
    search_fields = ["title"]
    ordering_fields = ["due_date", "created_at"]
    ordering = ["-created_at"]

    def get_throttles(self):
        if self.request.method == "POST":
            return [TaskRateThrottle()]
        return super().get_throttles()

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
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()
        queryset = Task.objects.filter(project= self.get_project())
        assigned_to = self.request.query_params.get("assigned_to")

        if assigned_to == "me":
            queryset = queryset.filter(assigned_to=self.request.user)
        elif assigned_to is not None:
            queryset = queryset.filter(assigned_to=assigned_to)

        return queryset
    
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

@extend_schema_view(
    get=extend_schema(
        tags=["Tasks"],
        summary="Retrieve a task",
        description="Returns details of a task. Only accessible to project members. Non-members receive 404."
    ),
    put=extend_schema(
        tags=["Tasks"],
        summary="Full update a task",
        description="Fully updates a task. Handles assignment, status change, and field updates as separate service calls. Events are recorded only if values actually changed."
    ),
    patch=extend_schema(
        tags=["Tasks"],
        summary="Partial update a task",
        description="Partially updates a task. Handles assignment, status change, and field updates as separate service calls. Events are recorded only if values actually changed."
    ),
    delete=extend_schema(
        tags=["Tasks"],
        summary="Delete a task",
        description="Deletes a task. Only accessible to project members."
    ),
)
class TaskDetailView(RetrieveUpdateDestroyAPIView):
    """
    Task detail endpoint.

    Methods:
    - GET    /api/v1/tasks/{id}/     -> Retrieve task details
    - PUT    /api/v1/tasks/{id}/     -> Full update
    - PATCH  /api/v1/tasks/{id}/     -> Partial update
    - DELETE /api/v1/tasks/{id}/     -> Delete task

    Permission: IsMember

    GET Response (200):
    {
        "id": 1,
        "title": "Fix the bug",
        "description": "Investigate and fix the login bug",
        "project": 1,
        "assigned_to": 2,
        "created_by": "user1",
        "status": "TODO",
        "due_date": "2026-04-01",
        "created_at": "2026-03-20T07:47:15Z"
    }

    PATCH Examples:

    1. Update title/description/due_date:
    {
        "title": "Updated title",
        "due_date": "2026-04-10"
    }

    2. Assign task:
    {
        "assigned_to": 2
    }

    3. Unassign task:
    {
        "assigned_to": null
    }

    4. Change status:
    {
        "status": "IN_PROGRESS"
    }

    DELETE Response:
    - 204 No Content

    Validation:
    - assigned_to must be a project member
    - status must be one of: TODO, IN_PROGRESS, DONE

    Notes:
    - Non-members receive 404 to avoid leaking task existence.
    - assign_task, change_status, and update_task are handled as separate service calls.
    - Events are recorded only if values actually changed.
    - An email notification is sent to the assignee via Celery on assignment.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsMember]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_throttles(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [TaskRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()
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

@extend_schema_view(
    get=extend_schema(
        tags=["Comments"],
        summary="List all comments for a task",
        description="Returns a paginated list of all comments for a task, ordered newest first. Only accessible to project members."
    ),
    post=extend_schema(
        tags=["Comments"],
        summary="Add a comment to a task",
        description="Creates a new comment on a task. The authenticated user is automatically set as author. Content cannot be empty."
    ),
)
class CommentListCreateView(ListCreateAPIView):
    """
    Comment list & creation endpoint.

    Methods:
    - GET  /api/v1/tasks/{id}/comments/   -> List all comments for a task
    - POST /api/v1/tasks/{id}/comments/   -> Create a new comment in the task

    Permission:
    - Project members only
    
    GET Response (200):
    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 1,
                "content": "Looks good to me!",
                "author": "user1",
                "created_at": "2026-03-20T07:47:15Z"
            }
        ]
    }
    
    POST Request:
    {
        "content": "Looks good to me!"
    }

    POST Response:
    {
        "id": 1,
        "content": "Great job!",
        "author": "user1",
        "created_at": "2026-03-20T07:47:15Z"
    }

    Validation:
    - content cannot be empty or whitespace only.

    Notes:
    - Non-members receive 403.
    - Task is taken from the URL, not the request body.
    - author is automatically set to the authenticated user.
    - Comments are ordered newest first.
    - A COMMENT_ADDED event is recorded on creation.
    - Results are paginated (default page size: 20).
    """

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        if self.request.method == "POST":
            return [CommentRateThrottle()]
        return super().get_throttles()

    def get_task(self):
        if not hasattr(self, "_task"):
            task = get_object_or_404(Task, pk=self.kwargs["id"])

            if not task.project.members.filter(id=self.request.user.id).exists():
                raise PermissionDenied("You are not a member of this project")
            
            self._task = task
        return self._task
    
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Comment.objects.none()
        return Comment.objects.filter(task=self.get_task())
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["task"] = self.get_task()
        return context
    
    def perform_create(self, serializer):
        try:
            comment = create_comment(
                user=self.request.user,
                task=self.get_task(),
                data=serializer.validated_data
            )
        except Exception as err:
            raise ValidationError({"detail": str(err)})
        serializer.instance = comment

@extend_schema_view(
    delete=extend_schema(
        tags=["Comments"],
        summary="Delete a comment",
        description="Deletes a comment. Only the comment author can perform this action. Non-members receive 404."
    ),
)    
class CommentDeleteView(DestroyAPIView):
    """
    Comment delete endpoint.

    Methods:
    - DELETE /api/v1/comments/{id}/   -> Delete a comment

    Permission: IsAuthor

    DELETE Response:
    - 204 No Content

    Errors:
    - 401: Unauthenticated request.
    - 403: User is not the comment author.
    - 404: Comment not found or user is not a project member.

    Notes:
    - Only the comment author can delete their comment.
    - Non-members receive 404 to avoid leaking comment existence.
    """

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsAuthor]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Comment.objects.none()
        return Comment.objects.filter(task__project__members=self.request.user)
    
    def perform_destroy(self, comment):
        delete_comment(
            user=self.request.user,
            task=comment.task,
            comment=comment
        )