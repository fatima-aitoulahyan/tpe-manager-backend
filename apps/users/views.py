from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from apps.users.models import PasswordResetCode
from .models import ConfigurationEmail
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
import string
from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer, ConfigurationEmailSerializer
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Compte créé avec succès.',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'message': 'Mot de passe modifié avec succès.'},
            status=status.HTTP_200_OK
        )


import logging
logger = logging.getLogger(__name__)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': "La clé 'refresh' est manquante dans le body."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            logger.warning(f"Logout avec token invalide (ignoré): {str(e)}")
        return Response(
            {'message': 'Déconnexion réussie.'},
            status=status.HTTP_200_OK
        )
class ConfigurationEmailView(generics.RetrieveUpdateAPIView):
    serializer_class = ConfigurationEmailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        config, _ = ConfigurationEmail.objects.get_or_create(
            user=self.request.user,
            defaults={
                'email_address': self.request.user.email
            }
        )
        return config




class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'message': 'Si cet email existe, un code a été envoyé.'
            })
        code = ''.join(random.choices(string.digits, k=6))
        PasswordResetCode.objects.filter(user=user).delete()
        PasswordResetCode.objects.create(
            user=user,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        send_mail(
            subject='Code de réinitialisation - TPE Manager',
            message=f"""Bonjour {user.prenom},

Votre code de réinitialisation de mot de passe est : {code}

Ce code expire dans 10 minutes.

Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.

Cordialement,
L'équipe TPE Manager""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({
            'message': 'Si cet email existe, un code a été envoyé.'
        })


class VerifyResetCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        code  = request.data.get('code')

        if not email or not code:
            return Response(
                {'error': 'Email et code requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Code invalide ou expiré.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            reset_code = PasswordResetCode.objects.get(
                user=user, code=code
            )
        except PasswordResetCode.DoesNotExist:
            return Response(
                {'error': 'Code invalide ou expiré.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if reset_code.expires_at < timezone.now():
            reset_code.delete()
            return Response(
                {'error': 'Code expiré. Demandez un nouveau code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({'message': 'Code valide.', 'valid': True})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email        = request.data.get('email')
        code         = request.data.get('code')
        new_password = request.data.get('new_password')

        if not all([email, code, new_password]):
            return Response(
                {'error': 'Email, code et nouveau mot de passe requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 8:
            return Response(
                {'error': 'Le mot de passe doit contenir au moins 8 caractères.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Code invalide ou expiré.'},
                status=status.HTTP_400_BAD_REQUEST
            )


        try:
            reset_code = PasswordResetCode.objects.get(
                user=user, code=code
            )
        except PasswordResetCode.DoesNotExist:
            return Response(
                {'error': 'Code invalide ou expiré.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if reset_code.expires_at < timezone.now():
            reset_code.delete()
            return Response(
                {'error': 'Code expiré. Demandez un nouveau code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        reset_code.delete()

        return Response({
            'message': 'Mot de passe réinitialisé avec succès.'
        })