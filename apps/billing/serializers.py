from rest_framework import serializers
from apps.clients.serializers import ClientSerializer
from .models import Facture, LigneFacture

class LigneFactureSerializer(serializers.ModelSerializer):
    total = serializers.ReadOnlyField()

    class Meta:
        model  = LigneFacture
        fields = ['id', 'libelle', 'prix_unitaire', 'quantite', 'total']
        read_only_fields = ['id']


class FactureSerializer(serializers.ModelSerializer):
    lignes          = LigneFactureSerializer(many=True)
    client_detail   = ClientSerializer(source='client', read_only=True)
    montant_ht      = serializers.SerializerMethodField()
    montant_ttc     = serializers.SerializerMethodField()
    montant_tva     = serializers.SerializerMethodField()
    reste_a_payer   = serializers.ReadOnlyField()
    est_issue_devis = serializers.ReadOnlyField()
    devis_numero    = serializers.CharField(source='devis.numero', read_only=True)

    class Meta:
        model  = Facture
        fields = [
            'id', 'numero', 'statut',
            'date_emission', 'date_echeance',
            'taux_tva', 'montant_total', 'montant_paye', 'reste_a_payer',
            'mode_paiement', 'conditions',
            'client', 'client_detail',
            'devis', 'devis_numero', 'est_issue_devis',
            'lignes', 'montant_ht', 'montant_ttc', 'montant_tva',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'date_emission',
            'montant_total', 'created_at', 'updated_at'
        ]

    def get_montant_ht(self, obj):
        return float(obj.calculer_montant_ht())

    def get_montant_ttc(self, obj):
        return float(obj.calculer_montant_ttc())

    def get_montant_tva(self, obj):
        return float(obj.calculer_montant_ttc() - obj.calculer_montant_ht())

    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes')
        facture     = Facture.objects.create(**validated_data)

        for ligne in lignes_data:
            LigneFacture.objects.create(facture=facture, **ligne)

        facture.montant_total = facture.calculer_montant_ttc()
        facture.save(update_fields=['montant_total'])
        return facture

    def update(self, instance, validated_data):
        lignes_data = validated_data.pop('lignes', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if lignes_data is not None:
            instance.lignes.all().delete()
            for ligne in lignes_data:
                LigneFacture.objects.create(facture=instance, **ligne)
            instance.montant_total = instance.calculer_montant_ttc()
            instance.save()
        return instance
class FactureListSerializer(serializers.ModelSerializer):
    client_nom  = serializers.SerializerMethodField()
    montant_ttc = serializers.SerializerMethodField()

    class Meta:
        model  = Facture
        fields = [
            'id', 'numero', 'statut',
            'date_emission', 'date_echeance',
            'client_nom', 'montant_ttc'
        ]

    def get_client_nom(self, obj):
        return str(obj.client)

    def get_montant_ttc(self, obj):
        return float(obj.calculer_montant_ttc())