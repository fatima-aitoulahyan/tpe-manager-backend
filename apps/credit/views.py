from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import DemandeFinancement, Justificatif
from .serializers import (
    DemandeFinancementSerializer,
    DemandeFinancementListSerializer,
    JustificatifSerializer,
    EligibiliteSerializer,
)
from .eligibilite import calculer_score_eligibilite
from .services.notifications import notifier_changement_statut
from django.utils import timezone


class EligibiliteView(generics.GenericAPIView):
    """
    GET /api/credit/eligibilite/
    Calcule le score de pré-éligibilité en temps réel
    """
    permission_classes = [IsAuthenticated]
    serializer_class    = EligibiliteSerializer

    def get(self, request):
        resultat = calculer_score_eligibilite(request.user)
        serializer = self.get_serializer(data=resultat)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class DemandeFinancementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return DemandeFinancementListSerializer
        return DemandeFinancementSerializer

    def get_queryset(self):
        qs = DemandeFinancement.objects.filter(
            user=self.request.user
        ).prefetch_related('justificatifs', 'offres')

        statut = self.request.query_params.get('statut')
        if statut:
            qs = qs.filter(statut=statut)

        return qs

    def perform_create(self, serializer):
        resultat = calculer_score_eligibilite(self.request.user)

        serializer.save(
            user=self.request.user,
            score_eligibilite=resultat['score'],
            niveau_eligibilite=resultat['niveau'],
            date_consentement=timezone.now(),
        )
        notifier_changement_statut(
            serializer.instance, 'SOUMISE')
    def update(self, request, *args, **kwargs):
        demande = self.get_object()
        if demande.statut != DemandeFinancement.StatutDemande.SOUMISE:
            return Response(
                {'error': 'Cette demande ne peut plus être modifiée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        demande = self.get_object()
        if demande.statut not in [
            DemandeFinancement.StatutDemande.SOUMISE,
            DemandeFinancement.StatutDemande.DOSSIER_INCOMPLET,
        ]:
            return Response(
                {'error': 'Cette demande ne peut plus être supprimée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    # ── POST /api/credit/{id}/upload_justificatif/ ──
    @action(detail=True, methods=['post'],
            url_path='upload_justificatif')
    def upload_justificatif(self, request, pk=None):
        demande = self.get_object()

        type_doc = request.data.get('type_document')
        fichier  = request.FILES.get('fichier')

        if not fichier:
            return Response(
                {'error': 'Aucun fichier fourni.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        justificatif = Justificatif.objects.create(
            demande=demande,
            type_document=type_doc,
            fichier=fichier,
            nom_fichier=fichier.name,
        )

        return Response(
            JustificatifSerializer(justificatif).data,
            status=status.HTTP_201_CREATED
        )

    # ── DELETE /api/credit/{id}/justificatif/{justificatif_id}/ ──
    @action(detail=True, methods=['delete'],
            url_path='justificatif/(?P<justificatif_id>[^/.]+)')
    def delete_justificatif(self, request, pk=None, justificatif_id=None):
        demande = self.get_object()
        try:
            justificatif = demande.justificatifs.get(id=justificatif_id)
            justificatif.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Justificatif.DoesNotExist:
            return Response(
                {'error': 'Justificatif introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

    # ── GET /api/credit/stats/ ──
    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = DemandeFinancement.objects.filter(user=request.user)

        by_status = {
            s.value: qs.filter(statut=s.value).count()
            for s in DemandeFinancement.StatutDemande
        }

        return Response({
            'total_demandes': qs.count(),
            'by_status': by_status,
        })

    # ── PATCH /api/credit/{id}/changer_statut/ (admin/interne) ──
    @action(detail=True, methods=['patch'], url_path='changer_statut')
    def changer_statut(self, request, pk=None):
        demande = self.get_object()
        nouveau_statut = request.data.get('statut')
        motif_refus    = request.data.get('motif_refus')

        statuts_valides = [s.value for s in DemandeFinancement.StatutDemande]
        if nouveau_statut not in statuts_valides:
            return Response(
                {'error': f'Statut invalide. Choisir parmi : {statuts_valides}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        demande.statut = nouveau_statut
        if nouveau_statut == DemandeFinancement.StatutDemande.DEFAVORABLE:
            demande.motif_refus = motif_refus
        demande.save()

        return Response(
            DemandeFinancementSerializer(demande).data
        )
