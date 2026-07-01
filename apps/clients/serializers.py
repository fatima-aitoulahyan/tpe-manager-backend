from apps.clients.models import Client
from rest_framework import serializers

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Client
        fields = [
            'id', 'nom', 'prenom',
            'nom_entreprise', 'ice',
            'email', 'telephone'
        ]
        read_only_fields = ['id']