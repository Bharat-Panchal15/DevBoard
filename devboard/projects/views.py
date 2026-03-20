from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from projects.models import Project
from projects.serializers import ProjectSerializer

class ProjectListCreateView(ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(members=user).distinct()