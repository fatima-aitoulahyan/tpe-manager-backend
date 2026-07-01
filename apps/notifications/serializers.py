from rest_framework import serializers
from .models import PreferencesNotification, NotificationInApp


class PreferencesNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PreferencesNotification
        fields = [
            'rappel_facture_impayee', 'rappel_facture_jours',
            'rappel_devis_expirant', 'rappel_devis_jours_avant',
            'rappel_declaration_fiscale',
            'rappel_cotisation_cnss',
            'notification_demande_credit',
            'canal_in_app', 'canal_push', 'canal_sms',
        ]

    def validate_rappel_facture_jours(self, value):
        if value < 1 or value > 30:
            raise serializers.ValidationError(
                'Doit être entre 1 et 30 jours.')
        return value

    def validate_rappel_devis_jours_avant(self, value):
        if value < 1 or value > 30:
            raise serializers.ValidationError(
                'Doit être entre 1 et 30 jours.')
        return value

class NotificationInAppSerializer(serializers.ModelSerializer):
    class Meta:
        model  = NotificationInApp
        fields = ['id', 'titre', 'corps', 'type',
                  'reference_id', 'lue', 'created_at']