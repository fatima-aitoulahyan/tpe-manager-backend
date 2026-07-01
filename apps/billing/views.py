# apps/factures/views.py
from decimal import Decimal

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from .models import Facture
from .serializers import FactureSerializer, FactureListSerializer
from utils.pdf import generer_pdf


class FacturePagination(PageNumberPagination):
    page_size             = 10
    page_size_query_param = 'page_size'
    max_page_size         = 50


class FactureViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class   = FacturePagination

    def get_serializer_class(self):
        if self.action == 'list':
            return FactureListSerializer
        return FactureSerializer

    def get_queryset(self):
        qs = Facture.objects.filter(
            user=self.request.user
        ).select_related('client', 'devis').prefetch_related('lignes')

        if self.action != 'list':
            return qs

        statut     = self.request.query_params.get('statut')
        client     = self.request.query_params.get('client')
        date_debut = self.request.query_params.get('date_debut')
        date_fin   = self.request.query_params.get('date_fin')
        if statut == 'ARCHIVE':
            qs = qs.filter(statut='ARCHIVE')
        elif statut and statut != 'ACTIVE':
            qs = qs.filter(statut=statut).exclude(statut='ARCHIVE')
        else:
            qs = qs.exclude(statut='ARCHIVE')

        if client:
            qs = qs.filter(client_id=client)
        if date_debut:
            qs = qs.filter(date_emission__gte=date_debut)
        if date_fin:
            qs = qs.filter(date_emission__lte=date_fin)

        return qs
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # ── POST /api/factures/{id}/change_status/ ──
    @action(detail=True, methods=['post'], url_path='change_status')
    def changer_statut(self, request, pk=None):
        print("DATA REÇUE:", request.data)
        facture        = self.get_object()
        nouveau_statut = request.data.get('status', '').strip()
        statuts_valides = Facture.StatutFacture.values
        print("STATUTS VALIDES:", statuts_valides)        # ← ajout
        print("NOUVEAU STATUT:", repr(nouveau_statut))
        if nouveau_statut not in statuts_valides:
            return Response(
                {'error': f'Statut invalide. Choisir parmi : {statuts_valides}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if (
                facture.statut == Facture.StatutFacture.PAYEE
                and nouveau_statut != Facture.StatutFacture.ARCHIVE
        ):
            return Response(
                {'error': 'Une facture payée ne peut plus changer de statut sauf vers ARCHIVE.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        facture.statut = nouveau_statut
        facture.save()
        return Response({
            'message': f'Statut changé en {nouveau_statut}',
            'status':  facture.statut
        })



    @action(detail=True, methods=['post'])
    def enregistrer_paiement(self, request, pk=None):
        facture = self.get_object()
        montant = request.data.get('montant')

        if montant is None:
            return Response({'error': 'Montant requis'}, status=400)

        try:
            montant = Decimal(str(montant))
        except Exception:
            return Response({'error': 'Montant invalide'}, status=400)

        if montant <= 0:
            return Response({'error': 'Le montant doit être positif'}, status=400)

        facture.montant_paye += montant
        facture.save()

        return Response({
            'montant_paye': facture.montant_paye,
            'reste_a_payer': facture.reste_a_payer,
            'statut': facture.statut,
        })
    # ── GET /api/factures/stats/ ──
    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs    = Facture.objects.filter(user=request.user)
        total = qs.count()

        by_status = {
            s.value: qs.filter(statut=s.value).count()
            for s in Facture.StatutFacture
        }

        total_ca      = sum(f.montant_total for f in qs)
        total_encaisse = sum(f.montant_paye for f in qs)

        return Response({
            'total_factures':   total,
            'by_status':        by_status,
            'total_ca':         total_ca,
            'total_encaisse':   total_encaisse,
            'total_impaye':     total_ca - total_encaisse,
        })

    # ── GET /api/factures/{id}/pdf/ ──
    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        facture = self.get_object()
        serializer = FactureSerializer(facture)
        path = generer_pdf('factures/facture_pdf.html', {
            'facture': serializer.data,
            'lignes':  serializer.data.get('lignes', []),
        })

        return FileResponse(
            open(path, 'rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"{facture.numero}.pdf"
        )