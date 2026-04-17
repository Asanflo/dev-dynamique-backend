from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


# Create your tests here.

# user inscription endpoint
class UserInscriptionTest(APITestCase):

    # donnees necessaires au test
    def setUp(self):
        self.url = reverse('user-inscription')

    def test_user_creation(self):
        data = {
            "email": "test@test.com",
            "password": "test123!",
            "confirm_password": "test123!",
            "regle_confidentialite": True,
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # verifier si l'utilisateur est cree
        self.assertTrue(
            User.objects.filter(email="test@test.com").exists()
        )