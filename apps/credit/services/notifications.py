
def notifier_changement_statut(demande, nouveau_statut):
    from apps.notifications.models import (
        NotificationInApp, PreferencesNotification, DeviceToken
    )
    from apps.notifications.fcm_service import send_push_notification

    try:
        prefs = PreferencesNotification.objects.get(user=demande.user)
    except PreferencesNotification.DoesNotExist:
        prefs = None

    messages = {
        'SOUMISE':           'Votre demande de financement a été soumise.',
        'EN_ANALYSE':         'Votre demande est en cours d\'analyse.',
        'FAVORABLE':          'Bonne nouvelle ! Votre demande a reçu une décision favorable.',
        'DEFAVORABLE':        'Votre demande a reçu une décision défavorable.',
        'DOSSIER_INCOMPLET':  'Votre dossier est incomplet. Merci de compléter les pièces manquantes.',
    }

    corps = messages.get(nouveau_statut, 'Mise à jour de votre demande.')

    if not prefs or prefs.notification_demande_credit:
        if not prefs or prefs.canal_in_app:
            NotificationInApp.objects.create(
                user=demande.user,
                titre='Demande de financement',
                corps=corps,
                type='credit',
                reference_id=str(demande.id),
            )

        if not prefs or prefs.canal_push:
            tokens = DeviceToken.objects.filter(
                user=demande.user
            ).values_list('token', flat=True)
            for token in tokens:
                send_push_notification(
                    token=token,
                    title='Demande de financement',
                    body=corps,
                    data={'type': 'credit', 'id': str(demande.id)},
                )
