from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import  Devis, LigneDevis
from .serializers import  DevisSerializer, DevisListSerializer
from django.http import FileResponse
from utils.pdf import generer_pdf
from rest_framework.pagination import PageNumberPagination

from ..billing.models import LigneFacture, Facture


class DevisPagination(PageNumberPagination):
    page_size            = 10
    page_size_query_param = 'page_size'
    max_page_size        = 50

class DevisViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class   = DevisPagination

    def get_serializer_class(self):
        if self.action == 'list':
            return DevisListSerializer
        return DevisSerializer

    def get_queryset(self):
        qs = Devis.objects.filter(
            user=self.request.user
        ).select_related('client').prefetch_related('lignes')

        if self.action != 'list':
            return qs

        statut = self.request.query_params.get('statut')
        client = self.request.query_params.get('client')
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')

        if statut:
            qs = qs.filter(statut=statut)
        else:
            qs = qs.exclude(statut='ARCHIVE')

        if client:
            qs = qs.filter(client_id=client)
        if date_debut:
            qs = qs.filter(date_creation__gte=date_debut)
        if date_fin:
            qs = qs.filter(date_creation__lte=date_fin)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # ── POST /api/devis/{id}/change_status/ ──
    @action(detail=True, methods=['post'], url_path='change_status')
    def changer_statut(self, request, pk=None):
        devis          = self.get_object()
        nouveau_statut = request.data.get('status')
        statuts_valides = [s.value for s in Devis.StatutDevis]

        if nouveau_statut not in statuts_valides:
            return Response(
                {'error': f'Invalid status. Choose from: {statuts_valides}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if devis.statut == Devis.StatutDevis.ACCEPTE:
            return Response(
                {'error': 'An accepted quote cannot change status anymore.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        devis.statut = nouveau_statut
        devis.save()
        return Response({
            'message': f'Status changed to {nouveau_statut}',
            'status': devis.statut
        })

    # ── POST /api/devis/{id}/duplicate/ ──
    @action(detail=True, methods=['post'], url_path='duplicate')
    def dupliquer(self, request, pk=None):
        devis  = self.get_object()
        lignes = list(devis.lignes.all())

        devis.pk     = None
        devis.numero = None
        devis.statut = Devis.StatutDevis.BROUILLON
        devis.save()

        for ligne in lignes:
            ligne.pk    = None
            ligne.devis = devis
            ligne.save()

        return Response(
            DevisSerializer(devis, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    # ── GET /api/devis/stats/ ──
    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs    = Devis.objects.filter(user=request.user)
        total = qs.count()

        by_status = {
            s.value: qs.filter(statut=s.value).count()
            for s in Devis.StatutDevis
        }

        accepted = by_status.get('ACCEPTE', 0)
        rate     = round((accepted / total * 100), 1) if total > 0 else 0

        return Response({
            'total_quotes':      total,
            'by_status':         by_status,
            'conversion_rate':   f"{rate}%",
        })

    # ── GET /api/devis/{id}/pdf/ ──
    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):


        devis = self.get_object()
        path  = generer_pdf('devis/devis_pdf.html', {
            'devis':  devis,
            'lignes': devis.lignes.all(),
        })
        return FileResponse(
            open(path, 'rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"{devis.numero}.pdf"
        )
    @action(detail=True, methods=['post'], url_path='convert_to_facture')
    def convert_to_facture(self, request, pk=None):
        devis = self.get_object()

        if hasattr(devis, 'facture') and devis.facture:
            return Response(
                {'error': 'Ce devis a déjà été converti en facture.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        facture = Facture.objects.create(
            user          = devis.user,
            client        = devis.client,
            devis         = devis,
            taux_tva      = devis.taux_tva,
            mode_paiement = devis.mode_paiement,
            conditions    = devis.conditions,
            statut        = Facture.StatutFacture.BROUILLON,
        )

        for ligne_devis in devis.lignes.all():
            LigneFacture.objects.create(
                facture       = facture,
                libelle       = ligne_devis.libelle,
                prix_unitaire = ligne_devis.prix_unitaire,
                quantite      = ligne_devis.quantite,
            )

        facture.montant_total = facture.calculer_montant_ttc()
        facture.save(update_fields=['montant_total'])

        devis.statut = Devis.StatutDevis.ACCEPTE
        devis.save(update_fields=['statut'])
        return Response(
            {'id': facture.id, 'numero': facture.numero},
            status=status.HTTP_201_CREATED
        )

