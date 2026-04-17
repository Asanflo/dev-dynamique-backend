from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer
from accounts.permissions import IsOwnerOrMemberOrReadOnly, IsOwnerOrMemberOrAssignee



class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrMemberOrReadOnly]

    def get_queryset(self):
        user = self.request.user

        return Project.objects.filter(
            Q(owner=user) | Q(members=user)
        ).prefetch_related('members').distinct()

    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)

        # owner toujours membre du projet
        project.members.add(self.request.user)

    @action(detail=True, methods=['get', 'post'])
    def tasks(self, request, pk=None):
        project = self.get_object()

        # sécurité : owner ou member peuvent voir
        if not (
            project.owner == request.user or
            project.members.filter(id=request.user.id).exists()
        ):
            return Response(
                {"detail": "Accès refusé"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 🔹 GET → lister les tasks
        if request.method == 'GET':
            tasks = Task.objects.filter(project=project)\
                .select_related('assignee')

            serializer = TaskSerializer(tasks, many=True)
            return Response(serializer.data)

        # 🔹 POST → créer une task
        if project.owner != request.user:
            return Response(
                {"detail": "Seul le owner peut créer"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TaskSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# endpoint pour les taches d'un projet
class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsOwnerOrMemberOrAssignee]

    def get_queryset(self):
        user = self.request.user

        return Task.objects.filter(
            Q(project__owner=user) | Q(project__members=user)
        ).select_related('project', 'assignee').distinct()

    def perform_create(self, serializer):
        project = serializer.validated_data['project']

        if project.owner != self.request.user:
            raise PermissionError("Seul le owner peut créer des tâches")

        serializer.save()