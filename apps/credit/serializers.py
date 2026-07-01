from rest_framework import serializers
from .models import DemandeFinancement, Justificatif, OffreFinancement


class JustificatifSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Justificatif
        fields = ['id', 'type_document', 'fichier',
                  'nom_fichier', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class OffreFinancementSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OffreFinancement
        fields = ['id', 'partenaire_nom', 'taux_interet',
                  'duree_mois', 'mensualite_estimee',
                  'url_portail', 'created_at']


class DemandeFinancementSerializer(serializers.ModelSerializer):
    justificatifs = JustificatifSerializer(many=True, read_only=True)
    offres        = OffreFinancementSerializer(many=True, read_only=True)
    type_financement_display = serializers.CharField(
        source='get_type_financement_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model  = DemandeFinancement
        fields = [
            'id', 'type_financement', 'type_financement_display',
            'montant_demande', 'duree_mois', 'objet_financement',
            'statut', 'statut_display', 'motif_refus',
            'score_eligibilite', 'niveau_eligibilite',
            'consentement_cndp', 'date_consentement',
            'date_demande', 'updated_at',
            'justificatifs', 'offres',
        ]
        read_only_fields = [
            'id', 'statut', 'motif_refus',
            'score_eligibilite', 'niveau_eligibilite',
            'date_consentement', 'date_demande', 'updated_at',
        ]

    def validate_montant_demande(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Le montant doit être supérieur à 0.')
        return value

    def validate_duree_mois(self, value):
        if value not in DemandeFinancement.DUREES_VALIDES:
            raise serializers.ValidationError(
                f"Durée invalide. Choisir parmi : {DemandeFinancement.DUREES_VALIDES}")
        return value

    def validate_consentement_cndp(self, value):
        if not value:
            raise serializers.ValidationError(
                'Le consentement CNDP est obligatoire pour soumettre une demande.')
        return value

    def validate(self, attrs):
        type_fin = attrs.get('type_financement')
        montant  = attrs.get('montant_demande')

        if type_fin and montant:
            from .models import DemandeFinancement
            plafond = DemandeFinancement.PLAFONDS.get(type_fin)
            if plafond and montant > plafond:
                raise serializers.ValidationError({
                    'montant_demande':
                        f"Le montant dépasse le plafond indicatif de {plafond} MAD "
                        f"pour ce type de financement."
                })
        return attrs


class DemandeFinancementListSerializer(serializers.ModelSerializer):
    type_financement_display = serializers.CharField(
        source='get_type_financement_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model  = DemandeFinancement
        fields = [
            'id', 'type_financement_display', 'montant_demande',
            'duree_mois', 'statut', 'statut_display',
            'motif_refus', 'date_demande',
        ]


class EligibiliteSerializer(serializers.Serializer):
    score    = serializers.FloatField()
    niveau   = serializers.CharField()
    conseils = serializers.ListField(child=serializers.CharField())