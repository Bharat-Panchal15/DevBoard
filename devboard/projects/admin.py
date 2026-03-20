from django.contrib import admin
from projects.models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "owner", "created_at")
    search_fields = ("name",)
    list_filter = ("created_at",)