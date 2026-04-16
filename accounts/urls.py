from django.urls import path

from .views import UserInscriptionViewset

urlpatterns = [
    path("v1/inscription", UserInscriptionViewset.as_view()),
]