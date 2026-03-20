from rest_framework import serializers
from projects.models import Project

class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    members = serializers.PrimaryKeyRelatedField(read_only=True, many=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description", "owner", "members", "created_at"]
        read_only_fields = ["owner", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user

        # Create project with owner
        project = Project.objects.create(owner=user, **validated_data)

        # Add owner to members
        project.members.add(user)

        return project