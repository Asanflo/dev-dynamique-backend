from django.shortcuts import render
from rest_framework import status

from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import User
from .permissions import IsAdminRole
from .serializers import InscriptionUserSerializer, UserSerializer


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
            "username": response.data['username'],
        }, status=status.HTTP_201_CREATED)

# methode permettant d'effectuer des operations sur son profil
class UserDetailView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

#methode permettant d'afficher la liste des utilisateurs
class UserListView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]