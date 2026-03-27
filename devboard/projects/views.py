from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from projects.models import Project
from projects.serializers import ProjectSerializer, MemberSerializer
from projects.permissions import IsOwner
from projects.services import create_project, update_project, remove_project, add_member, remove_member

User = get_user_model()

class ProjectListCreateView(ListCreateAPIView):
    """
    Project list & creation endpoint.

    Methods:
    - GET  /api/projects/     -> List all projects for authenticated user
    - POST /api/projects/     -> Create a new project

    Permission: IsAuthenticated

    GET Response:
    [
        {
            "id": 1,
            "name": "DevBoard",
            "description": "Project desc",
            "owner": "user1",
            "members": [1],
            "created_at": "2026-03-20T07:47:15Z"
        }
    ]

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
    - Owner is automatically set to the authenticated user
    - Owner is automatically added to members
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(members=self.request.user).distinct()
    
    def perform_create(self, serializer):
        project = create_project(
            user=self.request.user,
            data=serializer.validated_data
        )
        serializer.instance = project

class ProjectDetailView(RetrieveUpdateDestroyAPIView):
    """
    Project detail endpoint.

    Methods:
    - GET    /api/projects/{id}/     -> Retrieve project details
    - PUT    /api/projects/{id}/     -> Update entire project
    - PATCH  /api/projects/{id}/     -> Partial update
    - DELETE /api/projects/{id}/     -> Delete project

    Permission:
    - GET: Project members only
    - PUT/PATCH/DELETE: Owner only

    GET Response:
    {
        "id": 1,
        "name": "DevBoard",
        "description": "Project desc",
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
    - Only project members can view
    - Only owner can update or delete
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(members=user).distinct()

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
    - GET  /api/projects/{id}/members/  -> List project members
    - POST /api/projects/{id}/members/  -> Add a member

    Permission:
    - GET: Project members only
    - POST: Owner only

    GET Response:
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

    POST Response:
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

    def get_project(self, id, user):
        """
        Fetch project only if user is a member.
        Otherwise return 404 (security).
        """
        return get_object_or_404(Project.objects.filter(members=user), id=id)
    
    def get(self, request, id):
        """
        GET /projects/{id}/members/
        List all members (only for project members)
        """
        project = self.get_project(id, request.user)
        members = project.members.all().values("id", "username", "email")

        return Response(members, status=status.HTTP_200_OK)
    
    def post(self, request, id):
        """
        POST /projects/{id}/members/
        Add a new member (only owner)
        """
        project = self.get_project(id, request.user)

        # 🔒 Only owner can add members
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
    - DELETE /api/projects/{id}/members/{user_id}/

    Permission:
    - Owner only

    Response:
    - 204 No Content

    Errors:
    {
        "detail": "Only owner can remove members"
    }

    {
        "detail": "Owner cannot be removed from the project"
    }

    {
        "detail": "User is not a member of this project"
    }

    Notes:
    - Owner cannot remove themselves
    - Only existing members can be removed
    """
    permission_classes = [IsAuthenticated]

    def get_project(self, id, user):
        """
        Fetch project only if user is a member.
        Otherwise return 404 (security).
        """
        return get_object_or_404(Project.objects.filter(members=user), id=id)
    
    def delete(self, request, id, user_id):
        """
        DELETE /projects/{id}/members/{user_id}/
        Only owner can remove members.
        """
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