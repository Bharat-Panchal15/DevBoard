from django.contrib import admin
from tasks.models import Task, Comment

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "project", "assigned_to", "status", "due_date")
    search_fields = ("title", "description")
    list_filter = ("status", "created_at")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "author", "content", "created_at")
    search_fields = ("content",)
    list_filter = ("created_at",)