from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from projects.models import Project
from tasks.models import Task

class DashboardView(APIView):
    """
    Dashboard summary endpoint.

    Methods:
    - GET /api/dashboard/ -> Retrieve summary statistics for the authenticated user

    Permission: IsAuthenticated

    Description:
    - Returns aggregated data related to the user's projects and tasks.
    - Only includes projects where the user is a member.
    - Tasks are counted across all those projects.

    Response:
    {
      "total_projects": 4,
      "total_tasks": 25,
      "completed_tasks": 9
    }

    Notes:
    - Uses database-level aggregation for efficiency.
    - Avoids loading all tasks into memory.
    - "completed_tasks" only counts tasks with status = "DONE".
    """
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