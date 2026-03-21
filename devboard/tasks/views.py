from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from tasks.serializers import TaskSerializer
from tasks.models import Task
from tasks.permissions import IsMember
from projects.models import Project

class TaskListCreateView(ListCreateAPIView):
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
        project = self.get_project()
        return Task.objects.filter(project=project)
    
    def get_serializer_context(self):
        """Pass project to serializer"""
        context = super().get_serializer_context()
        context["project"] = self.get_project()
        return context

class TaskDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsMember]
    lookup_field = "id"

    def get_queryset(self):
        return Task.objects.all()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["project"] = self.get_object().project
        return context