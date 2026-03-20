from django.urls import path
from projects.views import ProjectListCreateView

urlpatterns = [
    path("projects/", ProjectListCreateView.as_view(), name="projects"),
]