from rest_framework.permissions import BasePermission, SAFE_METHODS


# administrateur
class IsAdminRole(BasePermission):
    def has_object_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

# responsable ou membre d'un projet
class IsOwnerOrMemberOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        # lecture autorisée pour owner + members
        if request.method in SAFE_METHODS:
            return obj.owner == user or obj.members.filter(id=user.id).exists()
        # modification seulement owner
        return obj.owner == user

#  responsable du projet ou utilisateur a qui la tache est assigne
class IsOwnerOrMemberOrAssignee(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user

        if request.method in SAFE_METHODS:
            return (
                obj.project.owner == user or
                obj.project.members.filter(id=user.id).exists()
            )

        # write actions
        return obj.project.owner == user or obj.assignee == user