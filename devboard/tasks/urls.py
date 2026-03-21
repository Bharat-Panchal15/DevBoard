from django.urls import path
from tasks.views import TaskListCreateView, TaskDetailView

urlpatterns = [
    path("projects/<int:id>/tasks/", TaskListCreateView.as_view(), name="project-tasks"),
    path("tasks/<int:id>/", TaskDetailView.as_view(), name="task-detail"),
]