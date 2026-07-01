from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire")
        email = self.normalize_email(email)
        extra_fields.pop('username', None)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser doit avoir is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)

    ice = models.CharField(max_length=15, blank=True, null=True)
    statut_fiscal = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ('auto_entrepreneur', 'Auto-entrepreneur'),
            ('tpe', 'TPE'),
            ('artisan', 'Artisan'),
            ('freelance', 'Freelance'),
            ('commercant', 'Commerçant'),
        ]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom', 'telephone']

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return self.email

class ConfigurationEmail(models.Model):
    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='config_email')
    email_host     = models.CharField(max_length=100, default='smtp.gmail.com')
    email_port     = models.IntegerField(default=587)
    email_use_tls  = models.BooleanField(default=True)
    email_address  = models.EmailField()
    email_password = models.CharField(max_length=255)

    def __str__(self):
        return f"Config email de {self.user.email}"

class PasswordResetCode(models.Model):
    user       = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='reset_codes')
    code       = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Code de réinitialisation'

    def __str__(self):
        return f"{self.user.email} - {self.code}"