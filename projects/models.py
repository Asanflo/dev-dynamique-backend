from django.db import models
from accounts.models import User

# project model
class Project(models.Model):
    title       = models.CharField(max_length=200)
    description = models.TextField(max_length=500, blank=True, null=True)
    owner       = models.ForeignKey(
                      User, on_delete=models.CASCADE,
                      related_name='owned_projects'
                  )
    members     = models.ManyToManyField(
                      User,
                      related_name='member_projects',
                      blank=True
                  )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    start_date  = models.DateField()
    end_date    = models.DateField()

    def __str__(self):
        return self.title

    def get_tasks_count(self):
        return self.tasks.count()


# task model
class Task(models.Model):
    STATUS_CHOICES = (
        ('todo',        'To do'),
        ('in_progress', 'In progress'),
        ('done',        'Done'),
    )

    task_name   = models.CharField(max_length=100)
    description = models.TextField(max_length=500, blank=True, null=True)
    project     = models.ForeignKey(
                      Project, on_delete=models.CASCADE,
                      related_name='tasks'
                  )
    assignee    = models.ForeignKey(
                      User, on_delete=models.SET_NULL,
                      null=True, blank=True,
                      related_name='assigned_tasks'
                  )
    status      = models.CharField(
                      max_length=20,
                      choices=STATUS_CHOICES,
                      default='todo',
                  )
    due_date    = models.DateField()
    limit_date  = models.DateField()

    def __str__(self):
        return self.task_name

    def change_status(self, new_status):
        valid_statuses = [choice[0] for choice in self.STATUS_CHOICES]
        if new_status not in valid_statuses:
            raise ValueError(f"Statut invalide : {new_status}")
        self.status = new_status
        self.save(update_fields=['status'])

# comment (avis sur une tache) model
class Comment(models.Model):
    task       = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content    = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.task}"