from rest_framework import serializers
from .models import Project, Task
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
        child=serializers.EmailField(),
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
        emails = validated_data.pop('members_emails', [])
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
        emails = validated_data.pop('members_emails', None)

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
class TaskSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source='project.title', read_only=True)

    assignee_username = serializers.CharField(
        source='assignee.username',
        read_only=True
    )

    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.none()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request')
        if request:
            user = request.user

            # seulement projets où il est owner
            self.fields['project'].queryset = Project.objects.filter(owner=user)

    def validate(self, attrs):
        project = attrs.get('project') or getattr(self.instance, 'project', None)
        assignee = attrs.get('assignee')

        if project and assignee:
            if (
                    assignee != project.owner and
                    assignee not in project.members.all()
            ):
                raise serializers.ValidationError({
                    "assignee": "Doit être membre du projet"
                })

        return attrs

    class Meta:
        model = Task
        fields = [
            'id',
            'task_name',
            'description',
            'project',
            'project_title',
            'assignee',
            'assignee_username',
            'status',
            'due_date',
            'limit_date'
        ]