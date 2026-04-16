from rest_framework import serializers

from BackDevStat.accounts.models import User


class InscriptionUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['nom_complet', 'email', 'password', 'confirm_password']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if not email:
            raise serializers.ValidationError({'email': "L'email est requis"})

        if not password or not confirm_password:
            raise serializers.ValidationError({
                'password': 'Les deux champs de mot de passe sont requis'
            })

        if password != confirm_password:
            raise serializers.ValidationError({
                'password': 'Les mots de passe ne correspondent pas'
            })

        return attrs

    # enregistrement d'un utilisateur
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        return user
