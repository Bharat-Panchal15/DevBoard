from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_projects") # user.owned_projects.all() → projects user owns
    members = models.ManyToManyField(User, related_name="projects") # user.projects.all() → projects user is member of
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name