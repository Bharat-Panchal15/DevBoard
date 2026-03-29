from rest_framework import serializers
from tasks.models import Task
from django.contrib.auth import get_user_model

User = get_user_model()

class TaskSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset = User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Task
        fields = ["id", "title", "description", "project", "assigned_to", "status", "created_at", "due_date"]
        read_only_fields = ["project", "created_at"]

    def validate_assigned_to(self, user):
        """
        Ensure assigned user is a member of the project.
        """
        project = self.context.get("project")

        if user and project and not project.members.filter(id=user.id).exists():
            raise serializers.ValidationError("User must be a member of this project")
        
        return user
    
    def validate_status(self, value):
        if value not in Task.StatusChoices.values:
            raise serializers.ValidationError("Invalid status")
        return value