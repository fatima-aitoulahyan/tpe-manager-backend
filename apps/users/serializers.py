from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from apps.users.models import ConfigurationEmail

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email', 'nom', 'prenom', 'telephone',
            'password', 'password_confirm',
            'ice', 'statut_fiscal'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {'password': 'Les mots de passe ne correspondent pas.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'nom', 'prenom', 'telephone',
            'ice', 'statut_fiscal',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'created_at', 'updated_at']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Ancien mot de passe incorrect.')
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

# apps/users/serializers.py
class ConfigurationEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigurationEmail
        fields = ['email_address', 'email_password', 'email_host', 'email_port']
        extra_kwargs = {
            'email_password': {'write_only': True}
        }