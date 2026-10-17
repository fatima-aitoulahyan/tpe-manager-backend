from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.devis.models import Devis, LigneDevis
from apps.billing.models import Facture, LigneFacture
from apps.clients.models import Client
from apps.clients.serializers import ClientSerializer
from apps.devis.serializers import LigneDevisSerializer
from apps.billing.serializers import LigneFactureSerializer

User = get_user_model()


class AdminUserListSerializer(serializers.ModelSerializer):
    nb_devis = serializers.IntegerField(read_only=True)
    nb_factures = serializers.IntegerField(read_only=True)
    nb_clients = serializers.IntegerField(read_only=True)
    ca_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, allow_null=True)
    derniere_activite = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'nom', 'prenom', 'telephone',
            'statut_fiscal', 'is_active', 'created_at', 'last_login',
            'nb_devis', 'nb_factures', 'nb_clients', 'ca_total', 'derniere_activite',
        ]


class AdminDevisSerializer(serializers.ModelSerializer):
    """Serializer léger utilisé pour la LISTE des devis d'un utilisateur (onglet admin)."""
    client_nom = serializers.SerializerMethodField()

    class Meta:
        model = Devis
        fields = ['id', 'numero', 'client_nom', 'date_validite', 'montant_total', 'statut', 'created_at']

    def get_client_nom(self, obj):
        return f"{obj.client.nom} {obj.client.prenom}".strip()


class AdminDevisDetailSerializer(serializers.ModelSerializer):
    """Serializer complet utilisé pour le DÉTAIL d'un devis côté admin.
    Reproduit la même forme que DevisSerializer (app devis) pour que
    DevisDetailPage.jsx affiche les mêmes informations en mode lecture seule.
    """
    lignes = LigneDevisSerializer(many=True, read_only=True)
    client_detail = ClientSerializer(source='client', read_only=True)
    montant_ht = serializers.SerializerMethodField()
    montant_ttc = serializers.SerializerMethodField()
    facture_id = serializers.SerializerMethodField()
    facture_numero = serializers.SerializerMethodField()

    class Meta:
        model = Devis
        fields = [
            'id', 'numero', 'statut',
            'date_creation', 'date_validite',
            'taux_tva', 'montant_total',
            'mode_paiement', 'conditions',
            'client', 'client_detail',
            'lignes', 'montant_ht', 'montant_ttc',
            'facture_id', 'facture_numero',
            'created_at', 'updated_at',
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


class AdminFactureSerializer(serializers.ModelSerializer):
    """Serializer léger utilisé pour la LISTE des factures d'un utilisateur (onglet admin)."""
    client_nom = serializers.SerializerMethodField()

    class Meta:
        model = Facture
        fields = ['id', 'numero', 'client_nom', 'date_echeance', 'montant_total', 'statut', 'created_at']

    def get_client_nom(self, obj):
        return f"{obj.client.nom} {obj.client.prenom}".strip()


class AdminFactureDetailSerializer(serializers.ModelSerializer):
    """Serializer complet utilisé pour le DÉTAIL d'une facture côté admin.
    Reproduit la même forme que FactureSerializer (app billing) pour que
    FactureDetailPage.jsx affiche les mêmes informations en mode lecture seule.
    """
    lignes = LigneFactureSerializer(many=True, read_only=True)
    client_detail = ClientSerializer(source='client', read_only=True)
    montant_ht = serializers.SerializerMethodField()
    montant_ttc = serializers.SerializerMethodField()
    montant_tva = serializers.SerializerMethodField()
    reste_a_payer = serializers.ReadOnlyField()
    est_issue_devis = serializers.ReadOnlyField()
    devis_numero = serializers.CharField(source='devis.numero', read_only=True)

    class Meta:
        model = Facture
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

    def get_montant_ht(self, obj):
        return float(obj.calculer_montant_ht())

    def get_montant_ttc(self, obj):
        return float(obj.calculer_montant_ttc())

    def get_montant_tva(self, obj):
        return float(obj.calculer_montant_ttc() - obj.calculer_montant_ht())


class AdminClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'nom', 'prenom', 'nom_entreprise', 'ice', 'email', 'telephone', 'created_at']