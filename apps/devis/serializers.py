from rest_framework import serializers

from apps.clients.serializers import ClientSerializer
from .models import Devis, LigneDevis




class LigneDevisSerializer(serializers.ModelSerializer):
    total = serializers.ReadOnlyField()

    class Meta:
        model  = LigneDevis
        fields = ['id', 'libelle', 'prix_unitaire', 'quantite', 'total']
        read_only_fields = ['id']


class DevisSerializer(serializers.ModelSerializer):
    lignes         = LigneDevisSerializer(many=True)
    client_detail  = ClientSerializer(source='client', read_only=True)
    montant_ht     = serializers.SerializerMethodField()
    montant_ttc    = serializers.SerializerMethodField()
    peut_convertir = serializers.ReadOnlyField(source='peut_etre_converti')
    facture_id     = serializers.SerializerMethodField()
    facture_numero = serializers.SerializerMethodField()

    class Meta:
        model  = Devis
        fields = [
            'id', 'numero', 'statut',
            'date_creation', 'date_validite',
            'taux_tva', 'montant_total',
            'mode_paiement', 'conditions',
            'client', 'client_detail',
            'lignes', 'montant_ht', 'montant_ttc',
            'peut_convertir',
            'facture_id',
            'facture_numero',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'date_creation',
            'montant_total', 'created_at', 'updated_at'
        ]

    def get_montant_ht(self, obj):
        return float(obj.calculer_montant_ht())

    def get_montant_ttc(self, obj):
        return float(obj.calculer_montant_ttc())

    def get_facture_id(self, obj):
        try:
            return obj.facture.id
        except Exception:
            return None

    def get_facture_numero(self, obj):
        try:
            return obj.facture.numero
        except Exception:
            return None

    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes')

        devis = Devis.objects.create(**validated_data)
        for ligne in lignes_data:
            LigneDevis.objects.create(devis=devis, **ligne)

        devis.montant_total = devis.calculer_montant_ttc()

        devis.save(update_fields=['montant_total'])

        return devis

    def update(self, instance, validated_data):
        lignes_data = validated_data.pop('lignes', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lignes_data is not None:
            instance.lignes.all().delete()
            for ligne in lignes_data:
                LigneDevis.objects.create(devis=instance, **ligne)
            instance.montant_total = instance.calculer_montant_ttc()
            instance.save()
        return instance

class DevisListSerializer(serializers.ModelSerializer):
    client_nom  = serializers.SerializerMethodField()
    montant_ttc = serializers.SerializerMethodField()

    class Meta:
        model  = Devis
        fields = [
            'id', 'numero', 'statut',
            'date_creation', 'date_validite',
            'client_nom', 'montant_ttc'
        ]

    def get_client_nom(self, obj):
        return str(obj.client)

    def get_montant_ttc(self, obj):
        return float(obj.calculer_montant_ttc())