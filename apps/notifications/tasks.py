from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from apps.notifications.models import (
    DeviceToken,
    PreferencesNotification,
    NotificationInApp
)

from apps.notifications.fcm_service import send_push_notification
from apps.notifications.sms_service import send_sms, format_phone_maroc
from apps.notifications.email_service import send_email_as_vendeur
from apps.billing.models import Facture


def _get_tokens(user):
    return list(
        DeviceToken.objects.filter(
            user=user
        ).values_list('token', flat=True)
    )


def _notifier_vendeur_push(tokens, titre, corps, data):
    for token in tokens:
        send_push_notification(
            token=token,
            title=titre,
            body=corps,
            data=data
        )


def _notifier_vendeur_in_app(user, titre, corps, type_notif, reference_id=None):
    NotificationInApp.objects.create(
        user=user,
        titre=titre,
        corps=corps,
        type=type_notif,
        reference_id=reference_id
    )


@shared_task
def rappel_factures_impayees():
    prefs_list = PreferencesNotification.objects.filter(
        rappel_facture_impayee=True
    ).select_related('user')

    for prefs in prefs_list:
        seuil = (
                timezone.now().date()
                - timedelta(days=prefs.rappel_facture_jours)
        )

        factures = Facture.objects.filter(
            user=prefs.user,
            statut__in=[
                'EN_ATTENTE',
                'ENVOYE',
                'PARTIELLEMENT_PAYEE'
            ],
            date_echeance=seuil
        ).select_related('client', 'user')

        vendeur_tokens = _get_tokens(prefs.user)

        for facture in factures:
            message_vendeur = (
                f"La facture #{facture.numero} de {facture.client.nom} "
                f"est en retard de paiement. Une relance client est recommandée."
            )

            message_client = (
                f"Bonjour {facture.client.nom}, sauf erreur de notre part, la facture "
                f"#{facture.numero} est arrivée à échéance. Nous vous remercions de bien vouloir régulariser son paiement."
            )

            if facture.client.email:
                success = send_email_as_vendeur(
                    vendeur=facture.user,
                    to=facture.client.email,
                    subject=f"Rappel : Facture #{facture.numero} en attente de paiement",
                    body=message_client
                )
                if not success and prefs.canal_in_app:
                    _notifier_vendeur_in_app(
                        user=prefs.user,
                        titre="Configuration email requise",
                        corps="Votre relance client n'a pas pu être envoyée : configurez votre email dans Paramètres.",
                        type_notif='config_manquante'
                    )

            # SMS CLIENT
            if prefs.canal_sms and facture.client.telephone:
                telephone = format_phone_maroc(facture.client.telephone)
                send_sms(to=telephone, message=message_client)

            # PUSH VENDEUR
            if prefs.canal_push and vendeur_tokens:
                _notifier_vendeur_push(
                    tokens=vendeur_tokens,
                    titre="Facture impayée",
                    corps=message_vendeur,
                    data={"type": "facture", "id": str(facture.id)}
                )

            # IN APP VENDEUR
            if prefs.canal_in_app:
                _notifier_vendeur_in_app(
                    user=prefs.user,
                    titre="Facture impayée",
                    corps=message_vendeur,
                    type_notif='facture',
                    reference_id=str(facture.id)
                )

@shared_task
def rappel_devis_expirants():
    from apps.devis.models import Devis

    prefs_list = PreferencesNotification.objects.filter(
        rappel_devis_expirant=True
    ).select_related('user')

    for prefs in prefs_list:
        date_cible = (
                timezone.now().date()
                + timedelta(days=prefs.rappel_devis_jours_avant)
        )

        devis_list = Devis.objects.filter(
            user=prefs.user,
            statut='ENVOYE',
            date_validite=date_cible
        ).select_related('client', 'user')

        vendeur_tokens = _get_tokens(prefs.user)

        for devis in devis_list:
            client = devis.client
            vendeur = devis.user
            message_vendeur = (
                f"Le devis #{devis.numero} destiné à {client.nom} "
                f"expire dans {prefs.rappel_devis_jours_avant} jours. "
                f"Pensez à relancer votre client."
            )

            # Message destiné au CLIENT (Email + SMS)
            message_client = (
                f"Bonjour {client.nom}, votre devis #{devis.numero} arrive à "
                f"échéance dans {prefs.rappel_devis_jours_avant} jours (le {devis.date_validite.strftime('%d/%m/%Y')}). "
                f"Nous restons à votre entière disposition pour toute question ou pour valider votre projet."
            )

            # EMAIL CLIENT
            if client.email:
                success = send_email_as_vendeur(
                    vendeur=vendeur,
                    to=client.email,
                    subject=f"Votre devis #{devis.numero} arrive bientôt à échéance",
                    body=message_client
                )
                if not success and prefs.canal_in_app:
                    _notifier_vendeur_in_app(
                        user=prefs.user,
                        titre="Configuration email requise",
                        corps="Votre relance client n'a pas pu être envoyée : configurez votre email dans Paramètres.",
                        type_notif='config_manquante'
                    )
            # SMS CLIENT
            if prefs.canal_sms and client.telephone:
                telephone = format_phone_maroc(client.telephone)
                send_sms(to=telephone, message=message_client)

            # PUSH VENDEUR
            if prefs.canal_push and vendeur_tokens:
                _notifier_vendeur_push(
                    tokens=vendeur_tokens,
                    titre="Devis expirant",
                    corps=message_vendeur,
                    data={
                        "type": "devis",
                        "id": str(devis.id)
                    }
                )

            # IN APP VENDEUR
            if prefs.canal_in_app:
                _notifier_vendeur_in_app(
                    user=prefs.user,
                    titre="Devis expirant",
                    corps=message_vendeur,
                    type_notif='devis',
                    reference_id=str(devis.id)
                )

@shared_task
def rappel_declaration_fiscale():
    aujourd_hui = timezone.now().date()

    if aujourd_hui.day != 19 or aujourd_hui.month != 6:
        return

    prefs_list = PreferencesNotification.objects.filter(user__is_active=True).select_related('user')

    for prefs in prefs_list:
        vendeur_tokens = _get_tokens(prefs.user)
        message = "C'est le moment de soumettre votre déclaration fiscale trimestrielle (TVA)."

        if prefs.canal_push and vendeur_tokens:
            _notifier_vendeur_push(
                tokens=vendeur_tokens,
                titre="Déclaration Fiscale",
                corps=message,
                data={"type": "fiscale"}
            )

        if prefs.canal_in_app:
            _notifier_vendeur_in_app(
                user=prefs.user,
                titre="Déclaration Fiscale",
                corps=message,
                type_notif='fiscale'
            )


@shared_task
def rappel_cotisation_cnss():
    aujourd_hui = timezone.now().date()

    if aujourd_hui.day != 19 or aujourd_hui.month != 6:
        return

    prefs_list = PreferencesNotification.objects.filter(user__is_active=True).select_related('user')

    for prefs in prefs_list:
        vendeur_tokens = _get_tokens(prefs.user)
        message = (
            "N'oubliez pas de déclarer et régler vos cotisations CNSS ce mois-ci."
        )
        if prefs.canal_push and vendeur_tokens:
            _notifier_vendeur_push(
                tokens=vendeur_tokens,
                titre="Cotisation CNSS",
                corps=message,
                data={"type": "cnss"}
            )

        if prefs.canal_in_app:
            _notifier_vendeur_in_app(
                user=prefs.user,
                titre="Cotisation CNSS",
                corps=message,
                type_notif='cnss'
            )