from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DemandeFinancementViewSet, EligibiliteView

router = DefaultRouter()
router.register('demandes', DemandeFinancementViewSet,
                basename='demandes-financement')

urlpatterns = [
    path('eligibilite/', EligibiliteView.as_view()),
    path('', include(router.urls)),
]