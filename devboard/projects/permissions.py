from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    """Allows access only to the project owner."""

    def has_object_permission(self, request, view, object):
        return object.owner == request.user