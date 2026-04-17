from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import Project

User = get_user_model()

class ProjectAPITestCase(APITestCase):

    def setUp(self):
        # users
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@mail.com",
            password="pass1234",
            regle_confidentialite=True
        )

        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@mail.com",
            password="pass1234",
            regle_confidentialite=True
        )

        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@mail.com",
            password="pass1234",
            regle_confidentialite=True
        )

        self.client.force_authenticate(user=self.owner)

        self.url = reverse("projects-list")

    # creation d'un projet
    def test_create_project_with_valid_emails(self):
        data = {
            "title": "Project X",
            "description": "Test project",
            "members_emails": ["user1@mail.com", "user2@mail.com"],
            "start_date": "2026-01-01",
            "end_date": "2026-02-01"
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        project = Project.objects.get(title="Project X")

        self.assertEqual(project.owner, self.owner)
        self.assertEqual(project.members.count(), 3)
        self.assertIn(self.user1, project.members.all())
        self.assertIn(self.user2, project.members.all())
        self.assertIn(self.owner, project.members.all())

    # emails inexistants
    def test_create_project_with_missing_emails(self):
        data = {
            "title": "Project Y",
            "members_emails": ["fake@mail.com"],
            "start_date": "2026-01-01",
            "end_date": "2026-02-01"
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("members_emails", response.data)

    # list de project d'un owner
    def test_owner_can_list_projects(self):
        Project.objects.create(
            title="P1",
            owner=self.owner,
            start_date="2026-01-01",
            end_date="2026-02-01"
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)