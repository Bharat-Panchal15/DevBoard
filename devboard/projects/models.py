from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_projects") # user.owned_projects.all() → projects user owns
    members = models.ManyToManyField(User, related_name="projects") # user.projects.all() → projects user is member of
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Event(models.Model):

    class ActionChoices(models.TextChoices):
        PROJECT_CREATED = "PROJECT_CREATED"
        PROJECT_UPDATED = "PROJECT_UPDATED"
        MEMBER_ADDED = "MEMBER_ADDED"
        MEMBER_REMOVED = "MEMBER_REMOVED"
        TASK_CREATED = "TASK_CREATED"
        TASK_UPDATED = "TASK_UPDATED"
        TASK_ASSIGNED = "TASK_ASSIGNED"
        STATUS_UPDATED = "STATUS_UPDATED"
        COMMENT_ADDED = "COMMENT_ADDED"

    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events")
    action = models.CharField(max_length=50, choices=ActionChoices.choices)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="events")
    task = models.ForeignKey("tasks.Task", on_delete=models.CASCADE, null=True, blank=True, related_name="events")
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="targeted_events")
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.actor} - {self.action}"