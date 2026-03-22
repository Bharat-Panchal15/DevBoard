from django.urls import path
from projects.views import ProjectListCreateView, ProjectDetailView, ProjectMembersView, RemoveMemberView

urlpatterns = [
    path("projects/", ProjectListCreateView.as_view(), name="projects"),
    path("projects/<int:id>/", ProjectDetailView.as_view(), name="project-detail"),
    path("projects/<int:id>/members/", ProjectMembersView.as_view(), name="project-members"),
    path("projects/<int:id>/members/<int:user_id>/", RemoveMemberView.as_view(), name="remove-member"),
]