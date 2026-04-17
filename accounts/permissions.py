from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminRole(BasePermission):
    def has_object_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsOwnerOrMemberOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        # lecture autorisée pour owner + members
        if request.method in SAFE_METHODS:
            return obj.owner == user or obj.members.filter(id=user.id).exists()
        # modification seulement owner
        return obj.owner == user