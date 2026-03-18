from rest_framework.permissions import BasePermission

class IsAnonymous(BasePermission):
    """Allows access only to anonymous(unauthenticated) user"""

    def has_permission(self, request, view):
        return not request.user.is_authenticated