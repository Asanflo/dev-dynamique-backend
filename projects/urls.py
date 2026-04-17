from django.urls import path, include

from rest_framework import routers

from .views import ProjectViewSet, TaskViewSet

router = routers.DefaultRouter()

# Les routes pour les projets
router.register('projects', ProjectViewSet, basename='projects')
router.register('tasks', TaskViewSet, basename='tasks')

urlpatterns = [
    path("", include(router.urls)),
]