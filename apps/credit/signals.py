from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import DemandeFinancement
from .services.notifications import notifier_changement_statut


@receiver(pre_save, sender=DemandeFinancement)
def notifier_si_statut_change(sender, instance, **kwargs):

    if not instance.pk:
        return

    old = DemandeFinancement.objects.get(pk=instance.pk)

    if old.statut != instance.statut:
        notifier_changement_statut(instance, instance.statut)