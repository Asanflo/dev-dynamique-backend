from rest_framework import serializers

from .models import User


class InscriptionUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'regle_confidentialite']
        read_only_fields = ['username']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        regle_confidentialite = attrs.get('regle_confidentialite')

        if not email:
            raise serializers.ValidationError({'email': "L'email est requis"})

        if not password or not confirm_password:
            raise serializers.ValidationError({
                'password': 'Les deux champs de mot de passe sont requis'
            })
        if regle_confidentialite is not True:
            raise serializers.ValidationError({
                'regle_confidentialite': 'la règle de confidentialité doit être validée'
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


# Serializer to see user data and update it
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'nom_complet','avatar', 'bio', 'regle_confidentialite', 'created_at', 'updated_at', 'password', 'confirm_password']
        read_only_fields = ['regle_confidentialite','created_at', 'updated_at']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        confirm_password = validated_data.pop('confirm_password', None)

        if password:
            if password != confirm_password:
                raise serializers.ValidationError({
                    'password': 'Les deux password ne correspondent pas'
                })

            instance.set_password(password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance
