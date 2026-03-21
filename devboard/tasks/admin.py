from django.contrib import admin
from tasks.models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "project", "assigned_to", "status", "due_date")
    search_fields = ("title", "description")
    list_filter = ("status", "created_at")