from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
User = get_user_model()


class DemandeFinancement(models.Model):

    class TypeFinancement(models.TextChoices):
        FONCTIONNEMENT = 'FONCTIONNEMENT', 'Crédit de fonctionnement'
        INVESTISSEMENT = 'INVESTISSEMENT', 'Crédit d\'investissement'
        AVANCE_FACTURE = 'AVANCE_FACTURE', 'Avance sur factures'

    class StatutDemande(models.TextChoices):
        SOUMISE          = 'SOUMISE',          'Soumise'
        EN_ANALYSE        = 'EN_ANALYSE',        'En cours d\'analyse'
        FAVORABLE         = 'FAVORABLE',         'Décision favorable'
        DEFAVORABLE       = 'DEFAVORABLE',       'Décision défavorable'
        DOSSIER_INCOMPLET = 'DOSSIER_INCOMPLET', 'Dossier incomplet'

    user   = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='demandes_financement')

    type_financement = models.CharField(
        max_length=20, choices=TypeFinancement.choices)
    montant_demande   = models.DecimalField(
        max_digits=12, decimal_places=2)
    duree_mois         = models.PositiveIntegerField()
    objet_financement   = models.TextField()

    statut = models.CharField(
        max_length=20, choices=StatutDemande.choices,
        default=StatutDemande.SOUMISE)
    motif_refus = models.TextField(blank=True, null=True)
    score_eligibilite   = models.DecimalField(
        max_digits=5, decimal_places=2, default=0)
    niveau_eligibilite   = models.CharField(
        max_length=10, blank=True, null=True)

    consentement_cndp = models.BooleanField(default=False)
    date_consentement   = models.DateTimeField(null=True, blank=True)

    date_demande = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Demande de financement'
        ordering     = ['-date_demande']

    def __str__(self):
        return f"Demande #{self.id} - {self.user.email} - {self.statut}"

    def save(self, *args, **kwargs):
        if self.consentement_cndp and not self.date_consentement:
            self.date_consentement = timezone.now()
        super().save(*args, **kwargs)

    DUREES_VALIDES = [3, 6, 12, 18, 24, 36]

    PLAFONDS = {
        'FONCTIONNEMENT': Decimal('200000'),
        'INVESTISSEMENT': Decimal('500000'),
        'AVANCE_FACTURE': Decimal('100000'),
    }


class Justificatif(models.Model):

    class TypeDocument(models.TextChoices):
        CIN              = 'CIN',              'CIN'
        RC_PATENTE        = 'RC_PATENTE',        'RC / Patente'
        RELEVE_BANCAIRE   = 'RELEVE_BANCAIRE',   'Relevé bancaire'
        AUTRE             = 'AUTRE',             'Autre'

    demande      = models.ForeignKey(
        DemandeFinancement, on_delete=models.CASCADE,
        related_name='justificatifs')
    type_document = models.CharField(
        max_length=20, choices=TypeDocument.choices)
    fichier      = models.FileField(upload_to='justificatifs/%Y/%m/')
    nom_fichier  = models.CharField(max_length=255)
    uploaded_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Justificatif'

    def __str__(self):
        return f"{self.nom_fichier} - {self.demande}"


class OffreFinancement(models.Model):
    demande       = models.ForeignKey(
        DemandeFinancement, on_delete=models.CASCADE,
        related_name='offres')
    partenaire_nom = models.CharField(max_length=150)
    taux_interet   = models.DecimalField(max_digits=5, decimal_places=2)
    duree_mois     = models.PositiveIntegerField()
    mensualite_estimee = models.DecimalField(
        max_digits=10, decimal_places=2)
    url_portail   = models.URLField(blank=True, null=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Offre de financement'

    def __str__(self):
        return f"{self.partenaire_nom} - {self.taux_interet}%"