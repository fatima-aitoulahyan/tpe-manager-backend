from datetime import date
from django.db.models import Count, Sum, Max, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .permissions import IsPlatformAdmin
from .serializers import AdminUserListSerializer
from apps.devis.models import Devis
from apps.billing.models import Facture
from apps.clients.models import Client
from apps.cashflow.models import Transaction
from apps.cashflow.serializers import TransactionSerializer
from .serializers import (
    AdminDevisSerializer,
    AdminDevisDetailSerializer,
    AdminFactureSerializer,
    AdminFactureDetailSerializer,
    AdminClientSerializer,
)

User = get_user_model()


class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsPlatformAdmin]
    serializer_class = AdminUserListSerializer

    def get_queryset(self):
        return User.objects.filter(role='tpe_owner').annotate(
            nb_devis=Count('devis', distinct=True),
            nb_factures=Count('factures', distinct=True),
            nb_clients=Count('clients', distinct=True),
            ca_total=Sum(
                'factures__montant_paye',
                filter=Q(factures__statut__in=['PAYEE', 'PARTIELLEMENT_PAYEE'])
            ),
            derniere_activite=Max('factures__created_at'),
        ).order_by('-created_at')


class AdminUserDetailView(generics.RetrieveAPIView):
    permission_classes = [IsPlatformAdmin]
    serializer_class = AdminUserListSerializer

    def get_queryset(self):
        return User.objects.filter(role='tpe_owner').annotate(
            nb_devis=Count('devis', distinct=True),
            nb_factures=Count('factures', distinct=True),
            nb_clients=Count('clients', distinct=True),
            ca_total=Sum(
                'factures__montant_total',
                filter=Q(factures__statut='PAYEE')
            ),
            derniere_activite=Max('factures__created_at'),
        )


class AdminToggleUserActiveView(APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk, role='tpe_owner')
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        user.is_active = not user.is_active
        user.save()
        return Response({
            'message': 'Statut mis à jour.',
            'is_active': user.is_active
        })


MOIS_LABELS_FR = [
    'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
    'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc',
]


def _premier_du_mois_il_y_a(n_mois, reference=None):
    """Retourne le date() du 1er jour du mois situé n_mois mois avant reference (sans dépendance externe)."""
    reference = reference or timezone.now().date()
    mois_absolu = reference.year * 12 + (reference.month - 1) - n_mois
    annee = mois_absolu // 12
    mois = mois_absolu % 12 + 1
    return date(annee, mois, 1)


class AdminDashboardStatsView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        total_users = User.objects.filter(role='tpe_owner').count()
        active_users = User.objects.filter(role='tpe_owner', is_active=True).count()

        # --- Série d'évolution sur les 12 derniers mois (inscriptions + CA encaissé) ---
        nb_mois = 12
        debut_periode = _premier_du_mois_il_y_a(nb_mois - 1)

        inscriptions_par_mois = (
            User.objects.filter(role='tpe_owner', created_at__date__gte=debut_periode)
            .annotate(mois=TruncMonth('created_at'))
            .values('mois')
            .annotate(total=Count('id'))
        )
        inscriptions_map = {i['mois'].date(): i['total'] for i in inscriptions_par_mois}

        ca_par_mois = (
            Facture.objects.filter(
                statut__in=['PAYEE', 'PARTIELLEMENT_PAYEE'],
                date_emission__gte=debut_periode,
            )
            .annotate(mois=TruncMonth('date_emission'))
            .values('mois')
            .annotate(total=Sum('montant_paye'))
        )
        ca_map = {c['mois']: float(c['total'] or 0) for c in ca_par_mois}
        evolution = []
        for i in range(nb_mois):
            mois_date = _premier_du_mois_il_y_a(nb_mois - 1 - i)
            evolution.append({
                'mois': mois_date.strftime('%Y-%m'),
                'label': f"{MOIS_LABELS_FR[mois_date.month - 1]} {mois_date.year}",
                'inscriptions': inscriptions_map.get(mois_date, 0),
                'ca': ca_map.get(mois_date, 0.0),
            })

        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'evolution': evolution,
        })


class AdminUserDevisListView(generics.ListAPIView):
    permission_classes = [IsPlatformAdmin]
    serializer_class = AdminDevisSerializer

    def get_queryset(self):
        return Devis.objects.filter(user_id=self.kwargs['pk']).order_by('-created_at')


class AdminUserFacturesListView(generics.ListAPIView):
    permission_classes = [IsPlatformAdmin]
    serializer_class = AdminFactureSerializer

    def get_queryset(self):
        return Facture.objects.filter(user_id=self.kwargs['pk']).order_by('-created_at')


class AdminUserClientsListView(generics.ListAPIView):
    permission_classes = [IsPlatformAdmin]
    serializer_class = AdminClientSerializer

    def get_queryset(self):
        return Client.objects.filter(user_id=self.kwargs['pk']).order_by('-created_at')


class AdminDevisDetailView(generics.RetrieveAPIView):
    permission_classes = [IsPlatformAdmin]
    serializer_class = AdminDevisDetailSerializer
    queryset = Devis.objects.select_related('client').prefetch_related('lignes').all()


class AdminFactureDetailView(generics.RetrieveAPIView):
    permission_classes = [IsPlatformAdmin]
    serializer_class = AdminFactureDetailSerializer
    queryset = Facture.objects.select_related('client', 'devis').prefetch_related('lignes').all()


class AdminUserTransactionsListView(generics.ListAPIView):
    """Liste (paginée, lecture seule) des transactions de trésorerie d'un utilisateur donné."""
    permission_classes = [IsPlatformAdmin]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        qs = Transaction.objects.filter(user_id=self.kwargs['pk'])

        type_t = self.request.query_params.get('type')
        categorie = self.request.query_params.get('categorie')
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')

        if type_t:
            qs = qs.filter(type=type_t)
        if categorie:
            qs = qs.filter(categorie=categorie)
        if date_debut:
            qs = qs.filter(date__gte=date_debut)
        if date_fin:
            qs = qs.filter(date__lte=date_fin)

        return qs


class AdminUserCashflowDashboardView(APIView):
    """Résumé du mois en cours (recettes/dépenses/solde) pour un utilisateur donné, vu par l'admin."""
    permission_classes = [IsPlatformAdmin]

    def get(self, request, pk):
        aujourd_hui = timezone.now().date()
        debut_mois = aujourd_hui.replace(day=1)

        qs = Transaction.objects.filter(user_id=pk, date__gte=debut_mois)

        recettes = qs.filter(type='RECETTE').aggregate(total=Sum('montant'))['total'] or 0
        depenses = qs.filter(type='DEPENSE').aggregate(total=Sum('montant'))['total'] or 0

        categories_recettes = {}
        categories_depenses = {}

        for t in qs.filter(type='RECETTE'):
            cat = t.categorie or 'AUTRE_RECETTE'
            categories_recettes[cat] = categories_recettes.get(cat, 0) + float(t.montant)

        for t in qs.filter(type='DEPENSE'):
            cat = t.categorie or 'AUTRE_DEPENSE'
            categories_depenses[cat] = categories_depenses.get(cat, 0) + float(t.montant)

        return Response({
            'recettes_mois': float(recettes),
            'depenses_mois': float(depenses),
            'solde': float(recettes - depenses),
            'categories_recettes': categories_recettes,
            'categories_depenses': categories_depenses,
        })