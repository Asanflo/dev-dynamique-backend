# Application Projects — Documentation API

Backend Django REST Framework pour la gestion de projets collaboratifs.

---

## Description

L'application **Projects** permet de gérer des projets, des tâches et des commentaires dans un contexte collaboratif. Elle est organisée autour de trois ressources principales :

- **Project** : un projet appartient à un owner et peut avoir plusieurs membres. Seul l'owner peut créer des tâches et gérer les membres.
- **Task** : une tâche appartient à un projet et peut être assignée à un membre. Elle possède un statut (`todo`, `in_progress`, `done`).
- **Comment** : un commentaire est associé à une tâche et peut être posté par tout membre ou owner du projet.

### Règles de gestion

- Un utilisateur ne voit que les projets dont il est owner ou membre.
- Seul l'owner peut modifier, supprimer un projet, créer des tâches, ajouter ou retirer des membres.
- Les membres peuvent lire les projets, les tâches et poster des commentaires.
- Un utilisateur extérieur au projet n'a accès à aucune ressource de ce projet.
- L'owner est automatiquement ajouté comme membre à la création du projet.
- L'owner ne peut pas être retiré des membres.

---

## Authentification

Tous les endpoints nécessitent une authentification JWT.

```
Authorization: Bearer <access_token>
```

---

## Endpoints — Projects

### `GET /api/projects/`

Liste tous les projets dont l'utilisateur connecté est owner ou membre.

**Données d'entrée :** aucune

**Réponse 200 :**
```json
[
  {
    "id": 1,
    "title": "Project X",
    "description": "Description du projet",
    "owner": {
      "username": "owner",
      "email": "owner@mail.com",
      "nom_complet": "John Doe"
    },
    "members": [
      { "username": "user1", "email": "user1@mail.com", "nom_complet": "Jane Doe" }
    ],
    "start_date": "2026-01-01",
    "end_date": "2026-02-01"
  }
]
```

---

### `POST /api/projects/`

Crée un nouveau projet. L'owner est automatiquement l'utilisateur connecté et est ajouté comme membre.

**Données d'entrée :**
```json
{
  "title": "Project X",
  "description": "Description optionnelle",
  "members_emails": ["user1@mail.com", "user2@mail.com"],
  "start_date": "2026-01-01",
  "end_date": "2026-02-01"
}
```

| Champ | Type | Requis | Description |
|---|---|---|---|
| `title` | string | oui | Titre du projet (max 200 chars) |
| `description` | string | non | Description (max 500 chars) |
| `members_emails` | list[email] | non | Emails des membres à ajouter |
| `start_date` | date (YYYY-MM-DD) | oui | Date de début |
| `end_date` | date (YYYY-MM-DD) | oui | Date de fin (doit être après start_date) |

**Réponse 201 :** objet projet créé (même format que GET)

**Réponse 400 — email introuvable :**
```json
{
  "members_emails": "Utilisateurs introuvables : ['ghost@mail.com']"
}
```

**Réponse 400 — dates invalides :**
```json
{
  "date": "La date doit être après start_date."
}
```

---

### `GET /api/projects/{id}/`

Récupère le détail d'un projet.

**Données d'entrée :** aucune

**Réponse 200 :** objet projet complet (même format que GET liste)

**Réponse 403 :** utilisateur ni owner ni membre

**Réponse 404 :** projet inexistant

---

### `PATCH /api/projects/{id}/`

Modifie partiellement un projet. Réservé à l'owner.

**Données d'entrée (tous optionnels) :**
```json
{
  "title": "Nouveau titre",
  "description": "Nouvelle description",
  "members_emails": ["user3@mail.com"],
  "end_date": "2026-03-01"
}
```

**Réponse 200 :** objet projet mis à jour

**Réponse 403 :** utilisateur non owner

---

### `PUT /api/projects/{id}/`

Remplace complètement un projet. Réservé à l'owner.

**Données d'entrée :** mêmes champs que POST (tous requis sauf `description` et `members_emails`)

**Réponse 200 :** objet projet mis à jour

**Réponse 403 :** utilisateur non owner

---

### `DELETE /api/projects/{id}/`

Supprime un projet et toutes ses tâches (CASCADE). Réservé à l'owner.

**Données d'entrée :** aucune

**Réponse 204 :** aucun contenu

**Réponse 403 :** utilisateur non owner

---

## Endpoints — Membres

### `POST /api/projects/{id}/add-member/`

Ajoute un membre au projet via son email. Réservé à l'owner.

**Données d'entrée :**
```json
{
  "email": "user2@mail.com"
}
```

**Réponse 200 :** objet projet mis à jour avec la nouvelle liste de membres

**Réponse 400 — déjà membre :**
```json
{
  "detail": "user2@mail.com est déjà membre de ce projet."
}
```

**Réponse 403 :** utilisateur non owner

**Réponse 404 :** email introuvable

---

### `POST /api/projects/{id}/remove-member/`

Retire un membre du projet via son email. Réservé à l'owner. L'owner lui-même ne peut pas être retiré.

**Données d'entrée :**
```json
{
  "email": "user1@mail.com"
}
```

**Réponse 200 :** objet projet mis à jour

**Réponse 400 — tentative de retirer l'owner :**
```json
{
  "detail": "Impossible de retirer le owner du projet."
}
```

**Réponse 400 — pas membre :**
```json
{
  "detail": "user1@mail.com n'est pas membre de ce projet."
}
```

**Réponse 403 :** utilisateur non owner

**Réponse 404 :** email introuvable

---

## Endpoints — Tasks

### `GET /api/projects/{id}/tasks/`

Liste toutes les tâches d'un projet. Accessible à l'owner et aux membres.

**Données d'entrée :** aucune

**Réponse 200 :**
```json
[
  {
    "id": 1,
    "task_name": "Tâche 1",
    "description": "Description de la tâche",
    "project": 1,
    "project_title": "Project X",
    "assignee": 2,
    "assignee_username": "user1",
    "status": "todo",
    "due_date": "2026-01-10",
    "limit_date": "2026-01-15"
  }
]
```

**Réponse 403 :** utilisateur ni owner ni membre

---

### `POST /api/projects/{id}/tasks/`

Crée une tâche dans le projet. Réservé à l'owner du projet.

**Données d'entrée :**
```json
{
  "task_name": "Tâche 1",
  "description": "Description optionnelle",
  "assignee": 2,
  "status": "todo",
  "due_date": "2026-01-10",
  "limit_date": "2026-01-15"
}
```

| Champ | Type | Requis | Description |
|---|---|---|---|
| `task_name` | string | oui | Nom de la tâche (max 100 chars) |
| `description` | string | non | Description (max 500 chars) |
| `assignee` | integer (ID) | non | ID d'un membre du projet |
| `status` | string | non | `todo` (défaut), `in_progress`, `done` |
| `due_date` | date | oui | Date prévue |
| `limit_date` | date | oui | Date limite |

**Réponse 201 :** objet tâche créée

**Réponse 400 — assignee non membre :**
```json
{
  "assignee": "L'assignee doit être membre du projet."
}
```

**Réponse 403 :** utilisateur non owner

---

### `GET /api/tasks/`

Liste toutes les tâches des projets dont l'utilisateur est owner ou membre.

**Paramètres de filtre (query string) :**

| Paramètre | Exemple | Description |
|---|---|---|
| `status` | `?status=todo` | Filtrer par statut |
| `assignee` | `?assignee=2` | Filtrer par assignee (ID) |

**Réponse 200 :** liste de tâches (même format que ci-dessus)

---

### `GET /api/tasks/{id}/`

Récupère le détail d'une tâche.

**Réponse 200 :** objet tâche

**Réponse 403 :** utilisateur sans accès au projet

**Réponse 404 :** tâche inexistante

---

### `PATCH /api/tasks/{id}/`

Modifie partiellement une tâche. Réservé à l'owner du projet ou à l'assignee.

**Données d'entrée (tous optionnels) :**
```json
{
  "status": "in_progress",
  "assignee": 3
}
```

**Réponse 200 :** objet tâche mis à jour

**Réponse 403 :** ni owner ni assignee

---

### `DELETE /api/tasks/{id}/`

Supprime une tâche. Réservé à l'owner du projet.

**Réponse 204 :** aucun contenu

**Réponse 403 :** utilisateur non owner

---

## Endpoints — Comments

### `POST /api/tasks/{id}/comments/`

Poste un commentaire sur une tâche. Accessible à l'owner et aux membres du projet.

**Données d'entrée :**
```json
{
  "content": "Contenu du commentaire"
}
```

| Champ | Type | Requis | Description |
|---|---|---|---|
| `content` | string | oui | Texte du commentaire (max 500 chars, non vide) |

**Réponse 201 :**
```json
{
  "id": 1,
  "task": 1,
  "author": 1,
  "author_username": "owner",
  "content": "Contenu du commentaire",
  "created_at": "2026-01-10T14:32:00Z"
}
```

**Réponse 400 — contenu vide :**
```json
{
  "content": ["Le contenu ne peut pas être vide."]
}
```

**Réponse 403 :** utilisateur ni owner ni membre du projet

---

### `GET /api/comments/`

Liste tous les commentaires des tâches accessibles à l'utilisateur connecté.

**Réponse 200 :** liste de commentaires (même format que ci-dessus)

---

## Codes de réponse — Résumé

| Code | Signification |
|---|---|
| 200 | Succès (lecture ou action) |
| 201 | Ressource créée |
| 204 | Suppression réussie |
| 400 | Données invalides |
| 401 | Non authentifié |
| 403 | Accès refusé (authentifié mais sans permission) |
| 404 | Ressource introuvable ou invisible pour cet utilisateur |

> **Note :** un utilisateur extérieur à un projet reçoit un `404` sur les ressources de ce projet (tâches, commentaires), même si elles existent. Ce comportement est intentionnel — il ne révèle pas l'existence de la ressource.

---

## Modèles de données

### Project

| Champ | Type | Description |
|---|---|---|
| `id` | integer | Identifiant auto |
| `title` | CharField(200) | Titre |
| `description` | TextField(500) | Description (optionnel) |
| `owner` | FK → User | Créateur du projet |
| `members` | M2M → User | Membres du projet |
| `start_date` | DateField | Date de début |
| `end_date` | DateField | Date de fin |
| `created_at` | DateTimeField | Date de création (auto) |
| `updated_at` | DateTimeField | Date de modification (auto) |

### Task

| Champ | Type | Description |
|---|---|---|
| `id` | integer | Identifiant auto |
| `task_name` | CharField(100) | Nom de la tâche |
| `description` | TextField(500) | Description (optionnel) |
| `project` | FK → Project | Projet parent |
| `assignee` | FK → User | Membre assigné (optionnel) |
| `status` | CharField | `todo` / `in_progress` / `done` |
| `due_date` | DateField | Date prévue |
| `limit_date` | DateField | Date limite |

### Comment

| Champ | Type | Description |
|---|---|---|
| `id` | integer | Identifiant auto |
| `task` | FK → Task | Tâche commentée |
| `author` | FK → User | Auteur du commentaire |
| `content` | TextField(500) | Contenu |
| `created_at` | DateTimeField | Date de création (auto) |