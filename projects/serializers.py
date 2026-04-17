from rest_framework import serializers
from .models import Project, Task, Comment
from accounts.models import User


# user affichage (lecture uniquement)
class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'nom_complet']


# project serializer
class ProjectSerializer(serializers.ModelSerializer):
    # lecture : détails des membres
    members = MemberSerializer(many=True, read_only=True)

    # écriture : emails des membres
    members_emails = serializers.ListField(
        child=serializers.EmailField(allow_blank=True),
        write_only=True,
        required=False
    )

    class Meta:
        model = Project
        fields = [
            'title',
            'description',
            'owner',
            'members',
            'members_emails',
            'start_date',
            'end_date'
        ]
        read_only_fields = ['owner']

    # validation dates
    def validate(self, attrs):
        start = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end = attrs.get('end_date', getattr(self.instance, 'end_date', None))

        if start and end and end < start:
            raise serializers.ValidationError({
                "date":"La doit être après start_date."
            })

        return attrs

    # create
    def create(self, validated_data):
        emails = [e for e in validated_data.pop('members_emails', []) if e.strip()]
        project = Project.objects.create(**validated_data)
        # recherche users
        users = User.objects.filter(email__in=emails)

        found_emails = set(users.values_list('email', flat=True))
        missing_emails = set(emails) - found_emails

        if missing_emails:
            raise serializers.ValidationError({
                "members_emails": f"Utilisateurs introuvables : {list(missing_emails)}"
            })

        project.members.add(*users)

        return project

    # update
    def update(self, instance, validated_data):
        raw_emails = validated_data.pop('members_emails', None)
        emails = [e for e in raw_emails if e.strip()] if raw_emails is not None else None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if emails is not None:
            # tester si les mails renseignes existent en bd
            users = User.objects.filter(email__in=emails)

            # liste des mails trouves
            found_emails = set(users.values_list('email', flat=True))
            # liste des mails non trouves
            missing_emails = set(emails) - found_emails

            # message d'erreurs s'il existe des mails non trouves
            if missing_emails:
                raise serializers.ValidationError({
                    "members_emails": f"Utilisateurs introuvables : {list(missing_emails)}"
                })

            instance.members.set(users)

        return instance

# task serializer
# Utilisé par TaskViewSet — project soumis par l'utilisateur, restreint au owner
class TaskSerializer(serializers.ModelSerializer):
    project_title     = serializers.CharField(source='project.title', read_only=True)
    assignee_username = serializers.CharField(source='assignee.username', read_only=True)

    project  = serializers.PrimaryKeyRelatedField(queryset=Project.objects.none())
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # restreint aux projets dont il est owner
            self.fields['project'].queryset = Project.objects.filter(
                owner=request.user
            )

    def validate(self, attrs):
        project  = attrs.get('project') or getattr(self.instance, 'project', None)
        assignee = attrs.get('assignee')

        if project and assignee:
            if (
                assignee != project.owner and
                not project.members.filter(id=assignee.id).exists()
            ):
                raise serializers.ValidationError({
                    "assignee": "L'assignee doit être membre du projet."
                })

        return attrs

    class Meta:
        model  = Task
        fields = [
            'id', 'task_name', 'description',
            'project', 'project_title',
            'assignee', 'assignee_username',
            'status', 'due_date', 'limit_date'
        ]


# Utilisé par ProjectViewSet.tasks() — project injecté par la vue via save()
class TaskCreateFromProjectSerializer(serializers.ModelSerializer):
    project_title     = serializers.CharField(source='project.title', read_only=True)
    assignee_username = serializers.CharField(source='assignee.username', read_only=True)
    project           = serializers.PrimaryKeyRelatedField(read_only=True)
    assignee          = serializers.PrimaryKeyRelatedField(
                            queryset=User.objects.all(),
                            required=False,
                            allow_null=True
                        )

    def validate(self, attrs):
        # project vient du contexte car read_only → pas dans attrs
        project  = self.context.get('project')
        assignee = attrs.get('assignee')

        if project and assignee:
            if (
                assignee != project.owner and
                not project.members.filter(id=assignee.id).exists()
            ):
                raise serializers.ValidationError({
                    "assignee": "L'assignee doit être membre du projet."
                })

        return attrs

    class Meta:
        model  = Task
        fields = [
            'id', 'task_name', 'description',
            'project', 'project_title',
            'assignee', 'assignee_username',
            'status', 'due_date', 'limit_date'
        ]

# comment serializer

class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(
        source='author.username',
        read_only=True
    )

    class Meta:
        model  = Comment
        fields = [
            'id',
            'task',
            'author',
            'author_username',
            'content',
            'created_at'
        ]
        read_only_fields = ['author', 'task', 'created_at']

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Le contenu ne peut pas être vide.")
        return value