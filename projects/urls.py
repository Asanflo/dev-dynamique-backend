from django.urls import path, include

from rest_framework import routers

from .views import ProjectViewSet, TaskViewSet, CommentViewSet

router = routers.DefaultRouter()

# Les routes pour les projets
router.register('projects', ProjectViewSet, basename='projects')
router.register('tasks', TaskViewSet, basename='tasks')
router.register('comments', CommentViewSet, basename='comments')

urlpatterns = [
    path("", include(router.urls)),
]