from django.db.models import Q
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Project
from .serializers import ProjectSerializer
from accounts.permissions import IsOwnerOrMemberOrReadOnly



class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrMemberOrReadOnly]

    def get_queryset(self):
        user = self.request.user

        # projets où l'utilisateur est owner OU membre
        return Project.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct()

    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)

        # Ajouter automatiquement le owner dans les members
        project.members.add(self.request.user)