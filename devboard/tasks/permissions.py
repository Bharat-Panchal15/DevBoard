from rest_framework.permissions import BasePermission

class IsMember(BasePermission):
    """
    Allow access only to project members."""

    def has_object_permission(self, request, view, obj):
        return obj.project.members.filter(id=request.user.id).exists()