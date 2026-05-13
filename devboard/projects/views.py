from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, serializers
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, inline_serializer
from projects.models import Project, Event
from projects.serializers import ProjectSerializer, MemberSerializer, EventSerializer
from projects.permissions import IsOwner
from projects.services import create_project, update_project, remove_project, add_member, remove_member
from projects.throttles import ProjectRateThrottle, MemberRateThrottle

User = get_user_model()

@extend_schema_view(
    get=extend_schema(
        tags=["Projects"],
        summary="List all projects",
        description="Returns a paginated list of all projects where the authenticated user is a member. Response is cached per user (TTL: 5 minutes)."
    ),
    post=extend_schema(
        tags=["Projects"],
        summary="Create a new project",
        description="Creates a new project. The authenticated user is automatically set as owner and added to members."
    ),
)
class ProjectListCreateView(ListCreateAPIView):
    """
    Project list & creation endpoint.

    Methods:
    - GET  /api/v1/projects/     -> List all projects for authenticated user
    - POST /api/v1/projects/     -> Create a new project

    Permission: IsAuthenticated

    GET Response (200):
    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 1,
                "name": "DevBoard",
                "description": "My backend project",
                "owner": "user1",
                "members": [1],
                "created_at": "2026-03-20T07:47:15Z"
            }
        ]
    }

    POST Request:
    {
        "name": "DevBoard",
        "description": "My backend project"
    }

    POST Response:
    {
        "id": 1,
        "name": "DevBoard",
        "description": "My backend project",
        "owner": "user1",
        "members": [1],
        "created_at": "2026-03-20T07:47:15Z"
    }

    Notes:
    - Only projects where the user is a member are returned. 
    - Owner is automatically set to the authenticated user
    - Owner is automatically added to members
    - Results are paginated (default page size: 20).
    - Response is cached per user (TTL: 5 minutes).
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        if self.request.method == "POST":
            return [ProjectRateThrottle()]
        return super().get_throttles()
    
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Project.objects.none()
        return Project.objects.filter(members=self.request.user).distinct()
    
    def perform_create(self, serializer):
        project = create_project(
            user=self.request.user,
            data=serializer.validated_data
        )
        serializer.instance = project
    
    def list(self, request, *args, **kwargs):
        cache_key = f"projects:user:{request.user.id}"
        cached = cache.get(cache_key)

        if cached:
            return Response(cached)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=300)
        
        return response

@extend_schema_view(
    get=extend_schema(
        tags=["Projects"],
        summary="Retrieve a project",
        description="Returns details of a project. Only accessible to project members. Non-members receive 404.",
    ),
    put=extend_schema(
        tags=["Projects"],
        summary="Full update a project",
        description="Fully updates a project. Only accessible to the project owner. An event is recorded only if fields actually changed.",
    ),
    patch=extend_schema(
        tags=["Projects"],
        summary="Partial update a project",
        description="Partially updates a project. Only accessible to the project owner. An event is recorded only if fields actually changed.",
    ),
    delete=extend_schema(
        tags=["Projects"],
        summary="Delete a project",
        description="Deletes a project and all its associated tasks and events. Only accessible to the project owner.",
    ),
)
class ProjectDetailView(RetrieveUpdateDestroyAPIView):
    """
    Project detail endpoint.

    Methods:
    - GET    /api/v1/projects/{id}/     -> Retrieve project details
    - PUT    /api/v1/projects/{id}/     -> Full update
    - PATCH  /api/v1/projects/{id}/     -> Partial update
    - DELETE /api/v1/projects/{id}/     -> Delete project

    Permission:
    - GET: Project members only
    - PUT/PATCH/DELETE: Project owner only

    GET Response (200):
    {
        "id": 1,
        "name": "DevBoard",
        "description": "My backend project",
        "owner": "user1",
        "members": [1, 2],
        "created_at": "2026-03-20T07:47:15Z"
    }

    PUT/PATCH Request:
    {
        "name": "Updated Name",
        "description": "Updated description"
    }

    DELETE Response:
    - 204 No Content

    Notes:
    - Non-members receive 404 (not 403) to avoid leaking project existence.
    - An event is recorded on update only if fields actually changed.
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_throttles(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [ProjectRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Project.objects.none()
        return Project.objects.filter(members=self.request.user).distinct()

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]
    
    def perform_update(self, serializer):
        try:
            project = update_project(
                user=self.request.user,
                project=self.get_object(),
                data=serializer.validated_data
            )
        except ValueError as err:
            raise ValidationError({"detail": str(err)})
        serializer.instance = project
    
    def perform_destroy(self, instance):
        try:
            remove_project(
                user=self.request.user,
                project=instance
            )
        except ValueError as err:
            raise ValidationError({"detail": str(err)})

class ProjectMembersView(APIView):
    """
    Project members management endpoint.

    Methods:
    - GET  /api/v1/projects/{id}/members/  -> List project members
    - POST /api/v1/projects/{id}/members/  -> Add a member

    Permission:
    - GET: Project members only
    - POST: Project owner only

    GET Response (200):
    [
        {
            "id": 1,
            "username": "user1",
            "email": "user1@example.com"
        }
    ]

    POST Request:
    {
        "user_id": 2
    }

    POST Response (201):
    {
        "detail": "Member added successfully"
    }

    Validation:
    - User must exist
    - User must not already be a member

    Notes:
    - Only project owner can add members
    """
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        if self.request.method == 'POST':
            return [MemberRateThrottle()]
        return super().get_throttles()

    def get_project(self, id, user):
        """
        Fetch project only if user is a member.
        Otherwise return 404 (security).
        """
        return get_object_or_404(Project.objects.filter(members=user), id=id)
    
    @extend_schema(
            tags=["Members"],
            responses={
                200: inline_serializer(
                    name="MemberListResponse",
                    fields={
                        "id": serializers.IntegerField(),
                        "username": serializers.CharField(),
                        "email": serializers.EmailField(),
                    }
                ),
                404: OpenApiResponse(description="Project not found or not a member"),
            },
            summary="List project members",
            description="Returns all members of a project. Only accessible to project members. Non-members receive 404."
    )
    def get(self, request, id):
        project = self.get_project(id, request.user)
        members = project.members.all().values("id", "username", "email")

        return Response(members, status=status.HTTP_200_OK)
    
    @extend_schema(
            tags=["Members"],
            request=MemberSerializer,
            responses={
                201: OpenApiResponse(description="Member added successfully"),
                400: OpenApiResponse(description="User does not exist or is already a member"),
                403: OpenApiResponse(description="Only the project owner can add members"),
                404: OpenApiResponse(description="Project not found or not a member"),
            },
            summary="Add a project member",
            description="Adds a new member to the project. Only the project owner can perform this action."
    )
    def post(self, request, id):
        project = self.get_project(id, request.user)

        if project.owner != request.user:
            return Response({"detail": "Only owner can add members"}, status=status.HTTP_403_FORBIDDEN)

        serializer = MemberSerializer(
            data=request.data,
            context={"request": request, "project": project}
        )

        if serializer.is_valid():
            member = serializer.validated_data["user_id"]

            try:
                add_member(
                    user=self.request.user,
                    project=project,
                    member=member
                )
            except ValueError as err:
                return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"detail": "Member added successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RemoveMemberView(APIView):
    """
    Remove project member endpoint.

    Methods:
    - DELETE /api/v1/projects/{id}/members/{user_id}/ -> Remove a member from the project

    Permission: IsOwner

    Response:
    - 204 No Content

    Errors:
    - 400: Owner cannot be removed from the project.
    - 400: User is not a member of this project.
    - 404: Project not found or requesting user is not a member.

    Notes:
    - Non-members receive 404 to avoid leaking project existence.
    - A MEMBER_REMOVED event is recorded on success.
    """
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        if self.request.method == "DELETE":
            return [MemberRateThrottle()]
        return super().get_throttles()

    def get_project(self, id, user):
        return get_object_or_404(Project.objects.filter(members=user), id=id)
    
    @extend_schema(
            tags=["Members"],
            responses={
                204: OpenApiResponse(description="Member removed successfully"),
                400: OpenApiResponse(description="Cannot remove owner or user is not a member"),
                403: OpenApiResponse(description="Only the project owner can remove members"),
                404: OpenApiResponse(description="Project not found or not a member"),
            },
            summary="Remove a project member",
            description="Removes a member from the project, Only the project owner can perform this action. Owner cannot be removed."
    )
    def delete(self, request, id, user_id):
        project = self.get_project(id, request.user)
        member = get_object_or_404(User, id=user_id)

        try:
            remove_member(
                user=self.request.user,
                project=project,
                member=member
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as err:
            return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(
    get=extend_schema(
        tags=["Events"],
        summary="List project events",
        description="Returns a paginated list of all events for a project, ordered newest first. Only accessible to project members. Response is cached per project (TTL: 5 minutes)."
    ),
)
class EventListView(ListAPIView):
    """
    Project event log endpoint.

    Methods:
    - GET /api/v1/projects/{id}/events/ -> List all events for a project.

    Permission:
    - Project members only

    GET Response (200):
    {
        "count": 2,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 1,
                "actor": "user1",
                "action": "TASK_CREATED",
                "task": 3,
                "target_user": null,
                "metadata": { "title": "Fix bug" },
                "created_at": "2026-03-20T07:47:15Z"
            }
        ]
    }

    Notes:
    - Non-members receive 404 to avoid leaking project existence.
    - Events are ordered newest first.
    - Results are paginated (default page size: 20).
    - Response is cached per project (TTL: 5 minutes).
    """

    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Event.objects.none()
        project = get_object_or_404(Project.objects.filter(members=self.request.user), id=self.kwargs["id"])

        return Event.objects.filter(project=project).order_by("-created_at")
    
    def list(self, request, *args, **kwargs):
        cache_key = f"events:project:{self.kwargs['id']}"
        cached = cache.get(cache_key)

        if cached:
            return Response(cached)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data)

        return response