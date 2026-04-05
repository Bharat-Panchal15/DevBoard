from rest_framework import serializers
from projects.models import Project, Event
from django.contrib.auth import get_user_model

User = get_user_model()

class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    members = serializers.PrimaryKeyRelatedField(read_only=True, many=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description", "owner", "members", "created_at"]
        read_only_fields = ["owner", "created_at"]

class MemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate_user_id(self, user_id):
        request = self.context.get("request")
        project = self.context.get("project")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        
        if project.members.filter(id=user.id).exists():
            raise serializers.ValidationError("User already a member")
        
        return user

class EventSerializer(serializers.ModelSerializer):
    actor = serializers.ReadOnlyField(source="actor.username")
    target_user = serializers.ReadOnlyField(source="target_user.username")

    class Meta:
        model = Event
        fields = ["id", "actor", "action", "task", "target_user", "metadata", "created_at"]
        read_only_fields = fields