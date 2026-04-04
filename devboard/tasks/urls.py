from django.urls import path
from tasks.views import TaskListCreateView, TaskDetailView, CommentListCreateView, CommentDetailView

urlpatterns = [
    path("projects/<int:id>/tasks/", TaskListCreateView.as_view(), name="project-tasks"),
    path("tasks/<int:id>/", TaskDetailView.as_view(), name="task-detail"),
    path("tasks/<int:id>/comments/", CommentListCreateView.as_view(), name="task-comments"),
    path("comments/<int:id>/", CommentDetailView.as_view(), name="comment-detail"),
]