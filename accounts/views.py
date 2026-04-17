from django.shortcuts import render
from rest_framework import status

from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import InscriptionUserSerializer


# Create your views here.

# methode permettant l'inscription d'un utilisateur
class UserInscriptionViewset(CreateAPIView):
    serializer_class = InscriptionUserSerializer
    permission_classes = [AllowAny]

    # override de la fonction create pour retourner un resultat specifique
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "message": "utilisateur créé",
            "status": status.HTTP_201_CREATED,
            "username": response.data['username'],
        })