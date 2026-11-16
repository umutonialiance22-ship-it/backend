from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    """Allow access only to users with the OPERATIONS_MANAGER role."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "OPERATIONS_MANAGER"
        )
