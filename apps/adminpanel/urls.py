from django.urls import path

from .views import (
    AdminUserListView, AdminUserDetailView, AdminToggleUserActiveView,
    AdminDashboardStatsView, AdminUserDevisListView,
    AdminUserFacturesListView, AdminUserClientsListView, AdminDevisDetailView, AdminFactureDetailView,
    AdminUserTransactionsListView, AdminUserCashflowDashboardView,
)

urlpatterns = [
    path('users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('users/<int:pk>/toggle-active/', AdminToggleUserActiveView.as_view(), name='admin-toggle-active'),
    path('users/<int:pk>/devis/', AdminUserDevisListView.as_view(), name='admin-user-devis'),
    path('users/<int:pk>/factures/', AdminUserFacturesListView.as_view(), name='admin-user-factures'),
    path('users/<int:pk>/clients/', AdminUserClientsListView.as_view(), name='admin-user-clients'),
    path('users/<int:pk>/cashflow/', AdminUserTransactionsListView.as_view(), name='admin-user-cashflow'),
    path('users/<int:pk>/cashflow/dashboard/', AdminUserCashflowDashboardView.as_view(), name='admin-user-cashflow-dashboard'),
    path('dashboard/', AdminDashboardStatsView.as_view(), name='admin-dashboard'),

    path('devis/<int:pk>/', AdminDevisDetailView.as_view(), name='admin-devis-detail'),
    path('factures/<int:pk>/', AdminFactureDetailView.as_view(), name='admin-facture-detail'),
]