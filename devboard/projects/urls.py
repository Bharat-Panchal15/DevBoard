from django.urls import path
from projects.views import ProjectListCreateView, ProjectDetailView

urlpatterns = [
    path("projects/", ProjectListCreateView.as_view(), name="projects"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
]