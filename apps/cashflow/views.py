from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from django.utils import timezone
from .models import Transaction
from .serializers import TransactionSerializer
from rest_framework.pagination import PageNumberPagination
class TransactionPagination(PageNumberPagination):
    page_size             = 20
    page_size_query_param = 'page_size'
    max_page_size         = 100
class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class   = TransactionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = TransactionPagination

    def get_queryset(self):
        qs = Transaction.objects.filter(user=self.request.user)

        # Filtres
        type_t     = self.request.query_params.get('type')
        categorie  = self.request.query_params.get('categorie')
        date_debut = self.request.query_params.get('date_debut')
        date_fin   = self.request.query_params.get('date_fin')

        if type_t:
            qs = qs.filter(type=type_t)
        if categorie:
            qs = qs.filter(categorie=categorie)
        if date_debut:
            qs = qs.filter(date__gte=date_debut)
        if date_fin:
            qs = qs.filter(date__lte=date_fin)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    # ── GET /api/tresorerie/dashboard/ ──
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        aujourd_hui = timezone.now().date()
        debut_mois  = aujourd_hui.replace(day=1)

        qs = Transaction.objects.filter(
            user=request.user,
            date__gte=debut_mois
        )

        recettes = qs.filter(type='RECETTE').aggregate(
            total=Sum('montant'))['total'] or 0
        depenses = qs.filter(type='DEPENSE').aggregate(
            total=Sum('montant'))['total'] or 0

        # Stats par catégorie
        categories_recettes = {}
        categories_depenses = {}

        for t in qs.filter(type='RECETTE'):
            cat = t.categorie or 'AUTRE_RECETTE'
            categories_recettes[cat] = categories_recettes.get(
                cat, 0) + float(t.montant)

        for t in qs.filter(type='DEPENSE'):
            cat = t.categorie or 'AUTRE_DEPENSE'
            categories_depenses[cat] = categories_depenses.get(
                cat, 0) + float(t.montant)

        return Response({
            'recettes_mois':        float(recettes),
            'depenses_mois':        float(depenses),
            'solde':                float(recettes - depenses),
            'categories_recettes':  categories_recettes,
            'categories_depenses':  categories_depenses,
        })