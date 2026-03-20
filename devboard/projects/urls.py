from django.urls import path
from projects.views import ProjectCreateView

urlpatterns = [
    path("projects/", ProjectCreateView.as_view(), name="project-create"),
]