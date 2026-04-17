from django.db.models import Q
from django.http import Http404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Project, Task, Comment
from .serializers import ProjectSerializer, TaskSerializer, CommentSerializer, TaskCreateFromProjectSerializer
from accounts.permissions import IsOwnerOrMemberOrReadOnly, IsOwnerOrMemberOrAssignee

from accounts.models import User


class ProjectViewSet(ModelViewSet):
    serializer_class   = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrMemberOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct().select_related('owner').prefetch_related('members')

    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)
        project.members.add(self.request.user)

    #  Tasks

    @action(detail=True, methods=['get', 'post'])
    def tasks(self, request, pk=None):
        project = self.get_object()

        if request.method == 'GET':
            tasks = Task.objects.filter(project=project).select_related('assignee')
            return Response(TaskSerializer(tasks, many=True, context={'request': request}).data)

        if project.owner != request.user:
            return Response(
                {"detail": "Seul le owner peut créer des tâches."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TaskCreateFromProjectSerializer(
            data=request.data,
            context={'request': request, 'project': project}  # ← project dans le contexte
        )
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Membres

    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        project = self.get_object()

        # Seul le owner peut gérer les membres
        if project.owner != request.user:
            return Response(
                {"detail": "Seul le owner peut ajouter des membres."},
                status=status.HTTP_403_FORBIDDEN
            )

        email = request.data.get('email')
        if not email:
            return Response(
                {"detail": "Le champ 'email' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": f"Aucun utilisateur trouvé avec l'email '{email}'."},
                status=status.HTTP_404_NOT_FOUND
            )

        if project.members.filter(id=user.id).exists():
            return Response(
                {"detail": f"{email} est déjà membre de ce projet."},
                status=status.HTTP_400_BAD_REQUEST
            )

        project.members.add(user)
        return Response(
            ProjectSerializer(project, context={'request': request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='remove-member')
    def remove_member(self, request, pk=None):
        project = self.get_object()

        # Seul le owner peut gérer les membres
        if project.owner != request.user:
            return Response(
                {"detail": "Seul le owner peut retirer des membres."},
                status=status.HTTP_403_FORBIDDEN
            )

        email = request.data.get('email')
        if not email:
            return Response(
                {"detail": "Le champ 'email' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": f"Aucun utilisateur trouvé avec l'email '{email}'."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Empêcher de retirer le owner
        if user == project.owner:
            return Response(
                {"detail": "Impossible de retirer le owner du projet."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not project.members.filter(id=user.id).exists():
            return Response(
                {"detail": f"{email} n'est pas membre de ce projet."},
                status=status.HTTP_400_BAD_REQUEST
            )

        project.members.remove(user)
        return Response(
            ProjectSerializer(project, context={'request': request}).data,
            status=status.HTTP_200_OK
        )


# endpoint pour les taches d'un projet
class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsOwnerOrMemberOrAssignee]

    def get_queryset(self):
        user = self.request.user

        return Task.objects.filter(
            Q(project__owner=user) | Q(project__members=user)
        ).select_related('project', 'assignee').distinct()

    def get_object(self):
        # Cherche la tâche sans passer par le queryset filtré
        try:
            obj = Task.objects.select_related('project__owner').get(pk=self.kwargs['pk'])
        except Task.DoesNotExist:
            raise Http404

        # Vérifie les permissions objet → 403 si accès refusé
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        project = serializer.validated_data['project']

        if project.owner != self.request.user:
            raise PermissionError("Seul le owner peut créer des tâches")

        serializer.save()

    @action(detail=True, methods=['post'])
    def comments(self, request, pk=None):
        task = self.get_object()

        project = task.project
        user = request.user

        # 🔐 sécurité : owner ou member uniquement
        if not (
                project.owner == user or
                project.members.filter(id=user.id).exists()
        ):
            return Response(
                {"detail": "Accès refusé"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CommentSerializer(
            data=request.data,
            context={
                'request': request,
                'task': task  # 🔥 important pour validation
            }
        )

        if serializer.is_valid():
            serializer.save(task=task, author=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return Comment.objects.filter(
            Q(task__project__owner=user) |
            Q(task__project__members=user)
        ).select_related('author', 'task').distinct()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
