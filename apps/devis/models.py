from django.db import models
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()

class Devis(models.Model):

    class StatutDevis(models.TextChoices):
        BROUILLON = 'BROUILLON', 'Draft'
        ENVOYE    = 'ENVOYE',    'Sent'
        ACCEPTE   = 'ACCEPTE',   'Accepted'
        REFUSE    = 'REFUSE',    'Refused'
        EXPIRE    = 'EXPIRE',    'Expired'
        ARCHIVE   = 'ARCHIVE',   'Archived'

    class ModePaiement(models.TextChoices):
        ESPECES      = 'ESPECES',      'Cash'
        VIREMENT     = 'VIREMENT',     'Bank Transfer'
        MOBILE_MONEY = 'MOBILE_MONEY', 'Mobile Money'

    user   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devis')
    client = models.ForeignKey('clients.Client', on_delete=models.PROTECT, related_name='devis')

    numero = models.CharField(max_length=20, blank=True)

    statut = models.CharField(
        max_length=20,
        choices=StatutDevis.choices,
        default=StatutDevis.BROUILLON
    )

    date_creation = models.DateField(auto_now_add=True)
    date_validite = models.DateField()

    taux_tva      = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    mode_paiement = models.CharField(max_length=20, choices=ModePaiement.choices)
    conditions    = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Quote'
        ordering     = ['-date_creation']
        unique_together = [['user', 'numero']]

    def __str__(self):
        return f"{self.numero} - {self.client} ({self.statut})"

    def _generer_numero(self):
        annee = date.today().year
        dernier = (
            Devis.objects
            .filter(user=self.user, numero__startswith=f"DEV-{annee}-")
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

        return f"DEV-{annee}-{suivant:03d}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        if self.pk:
            self.montant_total = self.calculer_montant_ttc()

        super().save(*args, **kwargs)

    def calculer_montant_ht(self):
        return sum(
            ligne.prix_unitaire * ligne.quantite
            for ligne in self.lignes.all()
        )

    def calculer_montant_ttc(self):
        ht = self.calculer_montant_ht()
        return ht * (1 + self.taux_tva / 100)

    @property
    def est_expire(self):
        return date.today() > self.date_validite and self.statut == self.StatutDevis.ENVOYE

    @property
    def peut_etre_converti(self):
        return self.statut == self.StatutDevis.ACCEPTE


class LigneDevis(models.Model):
    devis         = models.ForeignKey(Devis, on_delete=models.CASCADE, related_name='lignes')
    libelle       = models.CharField(max_length=200)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    quantite      = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Quote Line'

    def __str__(self):
        return f"{self.libelle} x{self.quantite}"

    @property
    def total(self):
        return self.prix_unitaire * self.quantite