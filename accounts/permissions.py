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

    def has_permission(self, request, view):
        # L'utilisateur doit être authentifié (redondant si IsAuthenticated
        # est déjà dans permission_classes, mais défense en profondeur)
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        is_project_member = (
            obj.project.owner == user or
            obj.project.members.filter(id=user.id).exists()
        )

        # Lecture + commentaires : owner ou member suffisent
        if request.method in SAFE_METHODS or getattr(view, 'action', None) == 'comments':
            return is_project_member

        # Écriture (PUT, PATCH, DELETE) : owner ou assignee
        return obj.project.owner == user or obj.assignee == user