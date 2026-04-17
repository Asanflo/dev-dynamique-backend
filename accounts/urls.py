from django.urls import path

from .views import UserInscriptionViewset, UserDetailView, UserListView

urlpatterns = [
    path("v1/inscription", UserInscriptionViewset.as_view(), name="user-inscription"),
    path('me/', UserDetailView.as_view(), name='user-me'),
    path('users/', UserListView.as_view(), name='user-list'),
]