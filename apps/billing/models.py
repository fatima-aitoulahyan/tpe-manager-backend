from django.db import models
from django.contrib.auth import get_user_model
from datetime import date
from apps.cashflow.models import Transaction
User = get_user_model()

class Facture(models.Model):

    class StatutFacture(models.TextChoices):
        BROUILLON           = 'BROUILLON',           'Brouillon'
        EN_ATTENTE          = 'EN_ATTENTE',           'En attente'
        PARTIELLEMENT_PAYEE = 'PARTIELLEMENT_PAYEE',  'Partiellement payée'
        PAYEE               = 'PAYEE',                'Payée'
        ENVOYE              = 'ENVOYE',               'Envoyée'
        ARCHIVE             = 'ARCHIVE',              'Archivée'

    class ModePaiement(models.TextChoices):
        ESPECES      = 'ESPECES',      'Cash'
        VIREMENT     = 'VIREMENT',     'Bank Transfer'
        MOBILE_MONEY = 'MOBILE_MONEY', 'Mobile Money'

    user   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='factures')
    client = models.ForeignKey('clients.Client', on_delete=models.PROTECT, related_name='factures')
    devis  = models.OneToOneField(
        'devis.Devis',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='facture'
    )
    numero = models.CharField(max_length=20, blank=True)
    statut = models.CharField(
        max_length=25,
        choices=StatutFacture.choices,
        default=StatutFacture.BROUILLON
    )
    date_emission = models.DateField(auto_now_add=True)
    date_echeance = models.DateField(null=True, blank=True)
    taux_tva       = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    montant_total  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_paye   = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    mode_paiement = models.CharField(max_length=20, choices=ModePaiement.choices, blank=True, null=True)
    conditions    = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Invoice'
        ordering     = ['-date_emission']
        unique_together = [['user', 'numero']]

    def __str__(self):
        return f"{self.numero} - {self.client} ({self.statut})"

    def _generer_numero(self):
        annee = date.today().year

        dernier = (
            Facture.objects
            .filter(user=self.user, numero__startswith=f"FAC-{annee}-")
            .order_by('-numero')
            .first()
        )

        if dernier:
            try:
                dernier_num = int(dernier.numero.split('-')[-1])
                suivant = dernier_num + 1
            except (ValueError, IndexError):
                suivant = 1
        else:
            suivant = 1

        return f"FAC-{annee}-{suivant:03d}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        if self.pk:
            try:
                ancien = Facture.objects.get(pk=self.pk)
                ancien_montant_paye = ancien.montant_paye
            except Facture.DoesNotExist:
                ancien_montant_paye = 0
        else:
            ancien_montant_paye = 0

        if self.pk:
            self.montant_total = self.calculer_montant_ttc()
        else:
            self.montant_total = 0

        if self.statut != self.StatutFacture.BROUILLON:
            self.statut = self._calculer_statut()

        super().save(*args, **kwargs)
        difference = self.montant_paye - ancien_montant_paye
        if difference > 0:
            Transaction.objects.create(
                user=self.user,
                type=Transaction.TypeTransaction.RECETTE,
                montant=difference,
                categorie=Transaction.Categorie.PAIEMENT_FACTURE,
                description=f"Paiement facture {self.numero}",
                date=date.today(),
                facture=self,
            )
    def calculer_montant_ht(self):
        return sum(ligne.prix_unitaire * ligne.quantite for ligne in self.lignes.all())

    def calculer_montant_ttc(self):
        ht = self.calculer_montant_ht()
        return ht * (1 + self.taux_tva / 100)

    def _calculer_statut(self):
        if self.statut == self.StatutFacture.ARCHIVE:
            return self.StatutFacture.ARCHIVE
        if self.statut == self.StatutFacture.ENVOYE and self.montant_paye <= 0:
            return self.StatutFacture.ENVOYE
        if self.montant_paye <= 0:
            return self.StatutFacture.EN_ATTENTE
        if self.montant_paye >= self.montant_total:
            return self.StatutFacture.PAYEE
        return self.StatutFacture.PARTIELLEMENT_PAYEE
    @property
    def reste_a_payer(self):
        return self.montant_total - self.montant_paye

    @property
    def est_issue_devis(self):
        return self.devis is not None


class LigneFacture(models.Model):
    facture       = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    libelle       = models.CharField(max_length=200)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    quantite      = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Invoice Line'

    def __str__(self):
        return f"{self.libelle} x{self.quantite}"

    @property
    def total(self):
        return self.prix_unitaire * self.quantite