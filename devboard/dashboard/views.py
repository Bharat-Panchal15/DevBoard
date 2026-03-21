from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from projects.models import Project
from tasks.models import Task

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        projects = Project.objects.filter(members=user).distinct()
        tasks = Task.objects.filter(project__in=projects)

        stats = tasks.aggregate(
            total_tasks = Count("id"),
            completed_tasks = Count("id", filter=Q(status="DONE"))
        )

        return Response({
            "total_projects": projects.count(),
            "total_tasks": stats["total_tasks"],
            "completed_tasks": stats["completed_tasks"]
        })