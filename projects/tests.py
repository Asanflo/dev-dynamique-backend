from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import Project, Task, Comment

User = get_user_model()

class ProjectAPITestCase(APITestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", email="owner@mail.com",
            password="pass1234", regle_confidentialite=True
        )
        self.user1 = User.objects.create_user(
            username="user1", email="user1@mail.com",
            password="pass1234", regle_confidentialite=True
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@mail.com",
            password="pass1234", regle_confidentialite=True
        )
        self.other = User.objects.create_user(
            username="other", email="other@mail.com",
            password="pass1234", regle_confidentialite=True
        )

        self.client.force_authenticate(user=self.owner)
        self.url = reverse("projects-list")

        # projet de base réutilisé dans plusieurs tests
        self.project = Project.objects.create(
            title="Project Base",
            owner=self.owner,
            start_date="2026-01-01",
            end_date="2026-02-01"
        )
        self.project.members.add(self.owner, self.user1)

        self.detail_url      = reverse("projects-detail",       args=[self.project.id])
        self.add_member_url  = reverse("projects-add-member",   args=[self.project.id])
        self.rem_member_url  = reverse("projects-remove-member",args=[self.project.id])
        self.tasks_url       = reverse("projects-tasks",        args=[self.project.id])

    # ─── Création ─────────────────────────────────────────────────────────────

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
        self.assertEqual(project.members.count(), 3)  # owner + user1 + user2
        self.assertIn(self.owner, project.members.all())
        self.assertIn(self.user1, project.members.all())
        self.assertIn(self.user2, project.members.all())

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

    def test_create_project_end_date_before_start_date(self):
        data = {
            "title": "Project Z",
            "start_date": "2026-03-01",
            "end_date": "2026-01-01"   # antérieure
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("date", response.data)

    def test_unauthenticated_cannot_create_project(self):
        self.client.force_authenticate(user=None)
        data = {
            "title": "Project Z",
            "start_date": "2026-01-01",
            "end_date": "2026-02-01"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ─── Liste & détail ───────────────────────────────────────────────────────

    def test_owner_can_list_projects(self):
        # setUp a déjà créé 1 projet (Project Base)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_member_can_see_project_in_list(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_outsider_cannot_see_project_in_list(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # liste vide

    def test_owner_can_retrieve_project(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Project Base")

    # ─── Modification ─────────────────────────────────────────────────────────

    def test_owner_can_update_project(self):
        response = self.client.patch(self.detail_url, {"title": "Nouveau titre"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Nouveau titre")

    def test_member_cannot_update_project(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(self.detail_url, {"title": "Tentative"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ─── Suppression ──────────────────────────────────────────────────────────

    def test_owner_can_delete_project(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(id=self.project.id).exists())

    def test_member_cannot_delete_project(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ─── Gestion des membres ──────────────────────────────────────────────────

    def test_owner_can_add_member(self):
        response = self.client.post(self.add_member_url, {"email": "user2@mail.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.user2, self.project.members.all())

    def test_add_member_already_in_project(self):
        response = self.client.post(self.add_member_url, {"email": "user1@mail.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_member_with_unknown_email(self):
        response = self.client.post(self.add_member_url, {"email": "ghost@mail.com"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_cannot_add_member(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.add_member_url, {"email": "user2@mail.com"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_remove_member(self):
        response = self.client.post(self.rem_member_url, {"email": "user1@mail.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.user1, self.project.members.all())

    def test_cannot_remove_owner_from_members(self):
        response = self.client.post(self.rem_member_url, {"email": "owner@mail.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_member_not_in_project(self):
        response = self.client.post(self.rem_member_url, {"email": "user2@mail.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_member_cannot_remove_member(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.rem_member_url, {"email": "user1@mail.com"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ─── Tasks ────────────────────────────────────────────────────────────────

    def test_owner_can_create_task(self):
        data = {
            "task_name": "Tâche 1",
            "due_date": "2026-01-10",
            "limit_date": "2026-01-15"
        }
        response = self.client.post(self.tasks_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.filter(project=self.project).count(), 1)

    def test_member_cannot_create_task(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            "task_name": "Tâche illégitime",
            "due_date": "2026-01-10",
            "limit_date": "2026-01-15"
        }
        response = self.client.post(self.tasks_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_list_tasks(self):
        Task.objects.create(
            task_name="Tâche visible",
            project=self.project,
            due_date="2026-01-10",
            limit_date="2026-01-15"
        )
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.tasks_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_outsider_cannot_list_tasks(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self.tasks_url)
        # outsider → get_object() lève 404 (tâche invisible dans son queryset)
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )

class TaskAPITestCase(APITestCase):

    def setUp(self):
        # users
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@mail.com",
            password="pass1234",
            regle_confidentialite=True
        )

        self.member = User.objects.create_user(
            username="member",
            email="member@mail.com",
            password="pass1234",
            regle_confidentialite=True
        )

        self.other = User.objects.create_user(
            username="other",
            email="other@mail.com",
            password="pass1234",
            regle_confidentialite=True
        )

        # project
        self.project = Project.objects.create(
            title="Project X",
            owner=self.owner,
            start_date="2026-01-01",
            end_date="2026-02-01"
        )
        self.project.members.add(self.owner, self.member)

        self.url = reverse("tasks-list")

    def test_owner_can_create_task(self):
        self.client.force_authenticate(user=self.owner)

        data = {
            "task_name": "Task 1",
            "project": self.project.id,
            "assignee": self.member.id,
            "due_date": "2026-01-10",
            "limit_date": "2026-01-15"
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)

    def test_member_cannot_create_task(self):
        self.client.force_authenticate(user=self.member)

        data = {
            "task_name": "Task 2",
            "project": self.project.id,
            "assignee": self.member.id,
            "due_date": "2026-01-10",
            "limit_date": "2026-01-15"
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_and_member_can_list_tasks(self):
        Task.objects.create(
            task_name="Task 1",
            project=self.project,
            due_date="2026-01-10",
            limit_date="2026-01-15"
        )

        # owner
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # member
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_member_cannot_see_tasks(self):
        Task.objects.create(
            task_name="Task 1",
            project=self.project,
            due_date="2026-01-10",
            limit_date="2026-01-15"
        )

        self.client.force_authenticate(user=self.other)
        response = self.client.get(self.url)

        self.assertEqual(len(response.data), 0)

    def test_assign_task_to_member(self):
        self.client.force_authenticate(user=self.owner)

        data = {
            "task_name": "Task assign",
            "project": self.project.id,
            "assignee": self.member.id,
            "due_date": "2026-01-10",
            "limit_date": "2026-01-15"
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class CommentAPITestCase(APITestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", email="owner@mail.com",
            password="pass1234", regle_confidentialite=True
        )
        self.member = User.objects.create_user(
            username="member", email="member@mail.com",
            password="pass1234", regle_confidentialite=True
        )
        self.other = User.objects.create_user(
            username="other", email="other@mail.com",
            password="pass1234", regle_confidentialite=True
        )

        self.project = Project.objects.create(
            title="Project X", owner=self.owner,
            start_date="2026-01-01", end_date="2026-02-01"
        )
        self.project.members.add(self.member)  # ← owner pas dans members, il est owner

        self.task = Task.objects.create(
            task_name="Task 1", project=self.project,
            due_date="2026-01-10", limit_date="2026-01-15"
        )

        self.task_comment_url = reverse("tasks-comments", args=[self.task.id])
        self.comment_list_url = reverse("comments-list")

    def test_owner_can_comment(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.task_comment_url, {"content": "Bon travail"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().author, self.owner)

    def test_member_can_comment(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(self.task_comment_url, {"content": "Je regarde ça"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_outsider_cannot_comment(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.post(self.task_comment_url, {"content": "Intrusion"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_comment(self):
        response = self.client.post(self.task_comment_url, {"content": "Sans auth"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_content_rejected(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.task_comment_url, {"content": "   "})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)