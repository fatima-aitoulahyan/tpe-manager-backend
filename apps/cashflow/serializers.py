from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    facture_numero = serializers.SerializerMethodField()

    def get_facture_numero(self, obj):
        return obj.facture.numero if obj.facture else None

    class Meta:
        model  = Transaction
        fields = [
            'id', 'type', 'montant', 'description',
            'categorie', 'date', 'created_at',
            'facture', 'facture_numero',
        ]
        read_only_fields = ['id', 'created_at', 'facture_numero']

    def validate_montant(self, value):
        if value <= 0:
            raise serializers.ValidationError('Le montant doit être supérieur à 0.')
        return value