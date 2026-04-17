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

    # test avec password et confirm_password differents
    def test_password_mismatch(self):
        data = {
            "email": "test@test.com",
            "password": "test123!",
            "confirm_password": "test12",
            "regle_confidentialite": True,
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    # tester une creation sans email
    def test_missing_email(self):
        data = {
            "password": "test123",
            "confirm_password": "test123",
            "regle_confidentialite": True,
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    # creation avec un email existant
    def test_existing_email(self):
        User.objects.create_user(
            email= "test@test.com",
            password= "test126",
            regle_confidentialite= True,
        )

        data = {
            "email": "test@test.com",
            "password": "test123!",
            "confirm_password": "test12",
            "regle_confidentialite": True,
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # creation sans regle de confidentialite
    def test_without_confidentialite_rule(self):
        data = {
            "email": "test@test.com",
            "password": "test123!",
            "confirm_password": "test12",
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("regle_confidentialite", response.data)