from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class PreferencesNotification(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='preferences_notifications')
    rappel_facture_impayee    = models.BooleanField(default=True)
    rappel_facture_jours      = models.PositiveIntegerField(default=3)

    rappel_devis_expirant     = models.BooleanField(default=True)
    rappel_devis_jours_avant  = models.PositiveIntegerField(default=3)

    rappel_declaration_fiscale = models.BooleanField(default=True)
    rappel_cotisation_cnss     = models.BooleanField(default=False)
    notification_demande_credit = models.BooleanField(default=True)

    canal_in_app = models.BooleanField(default=True)
    canal_push   = models.BooleanField(default=True)
    canal_sms    = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Préférences de notification'

    def __str__(self):
        return f"Préférences de {self.user.email}"

class DeviceToken(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    token      = models.CharField(max_length=255, unique=True)
    platform   = models.CharField(max_length=10, choices=[('android','Android'),('ios','iOS')], default='android')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} – {self.platform}"

class NotificationInApp(models.Model):

    class TypeNotif(models.TextChoices):
        FACTURE  = 'facture',  'Facture'
        DEVIS    = 'devis',    'Devis'
        FISCAL   = 'fiscal',   'Fiscal'
        CNSS     = 'cnss',     'CNSS'
        CREDIT   = 'credit',   'Crédit'

    user       = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications')
    titre      = models.CharField(max_length=200)
    corps      = models.TextField()
    type       = models.CharField(max_length=20, choices=TypeNotif.choices)
    reference_id = models.CharField(max_length=50, blank=True, null=True)
    lue        = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'

    def __str__(self):
        return f"{self.titre} - {self.user.email}"