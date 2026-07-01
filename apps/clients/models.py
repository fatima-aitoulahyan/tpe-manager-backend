from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class Client(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    nom           = models.CharField(max_length=100)
    prenom        = models.CharField(max_length=100, blank=True)
    nom_entreprise = models.CharField(max_length=150, blank=True, null=True)
    ice           = models.CharField(max_length=15, blank=True, null=True)
    email         = models.EmailField(blank=True, null=True)
    telephone     = models.CharField(max_length=20, blank=True, null=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Client'
        ordering     = ['nom']

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.nom_entreprise or 'Individual'})"
