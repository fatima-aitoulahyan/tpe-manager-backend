from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Transaction(models.Model):

    class TypeTransaction(models.TextChoices):
        RECETTE = 'RECETTE', 'Recette'
        DEPENSE = 'DEPENSE', 'Dépense'

    class Categorie(models.TextChoices):
        # Recettes
        PAIEMENT_FACTURE = 'PAIEMENT_FACTURE', 'Paiement facture'
        ACOMPTE          = 'ACOMPTE',          'Acompte'
        AUTRE_RECETTE    = 'AUTRE_RECETTE',     'Autre recette'
        # Dépenses
        ACHAT_MATERIEL   = 'ACHAT_MATERIEL',   'Achat matériel'
        LOYER            = 'LOYER',            'Loyer'
        SALAIRE          = 'SALAIRE',          'Salaire'
        TRANSPORT        = 'TRANSPORT',        'Transport'
        AUTRE_DEPENSE    = 'AUTRE_DEPENSE',    'Autre dépense'

    user        = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='transactions')
    type        = models.CharField(
        max_length=10, choices=TypeTransaction.choices)
    montant     = models.DecimalField(
        max_digits=12, decimal_places=2)
    description = models.CharField(max_length=200)
    categorie   = models.CharField(
        max_length=30, choices=Categorie.choices,
        blank=True, null=True)
    date        = models.DateField()
    created_at  = models.DateTimeField(auto_now_add=True)
    facture = models.ForeignKey(
        'billing.Facture',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transactions'
    )

    class Meta:
        verbose_name = 'Transaction'
        ordering     = ['-date', '-created_at']

    def __str__(self):
        return f"{self.type} - {self.montant} MAD - {self.date}"