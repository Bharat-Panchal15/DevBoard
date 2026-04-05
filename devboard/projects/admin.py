from django.contrib import admin
from projects.models import Project, Event

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "owner", "created_at")
    search_fields = ("name",)
    list_filter = ("created_at",)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "actor", "action", "project", "task", "target_user", "created_at")
    search_fields = ("actor__username", "action", "project__name", "task__title", "target_user__username")
    list_filter = ("action", "created_at")