from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from projects.models import Project
from projects.serializers import ProjectSerializer, MemberSerializer
from projects.permissions import IsOwner

User = get_user_model()

class ProjectListCreateView(ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(members=user).distinct()

class ProjectDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(members=user).distinct()

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]

class ProjectMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def get_project(self, pk, user):
        """
        Fetch project only if user is a member.
        Otherwise return 404 (security).
        """
        return get_object_or_404(Project.objects.filter(members=user), pk=pk)
    
    def get(self, request, pk):
        """
        GET /projects/{id}/members/
        List all members (only for project members)
        """
        project = self.get_project(pk, request.user)
        members = project.members.all().values("id", "username", "email")

        return Response(members, status=status.HTTP_200_OK)
    
    def post(self, request, pk):
        """
        POST /projects/{id}/members/
        Add a new member (only owner)
        """
        project = self.get_project(pk, request.user)

        # 🔒 Only owner can add members
        if project.owner != request.user:
            return Response(
                {"detail": "Only owner can add members"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MemberSerializer(
            data=request.data,
            context={"request": request, "project": project}
        )

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            project.members.add(user)

            return Response(
                {"detail": "Member added successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RemoveMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def get_project(self, pk, user):
        """
        Fetch project only if user is a member.
        Otherwise return 404 (security).
        """
        return get_object_or_404(Project.objects.filter(members=user), pk=pk)
    
    def delete(self, request, pk, user_id):
        """
        DELETE /projects/{id}/members/{user_id}/
        Only owner can remove members.
        """
        project = self.get_project(pk, request.user)

        # 🔒 Only owner can remove members
        if project.owner != request.user:
            return Response(
                {"detail": "Only owner can remove members"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # ❌ Prevent removing owner
        if project.owner.id == user_id:
            return Response(
                {"detail": "Owner cannot be removed from the project"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = get_object_or_404(User, id=user_id)

        # ❌ Check if user is actually a member
        if not project.members.filter(id=user.id).exists():
            return Response(
                {"detail": "User is not a member of this project"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        project.members.remove(user)

        return Response(status=status.HTTP_204_NO_CONTENT)