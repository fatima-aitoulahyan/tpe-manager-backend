from rest_framework.routers import DefaultRouter
from .views import FactureViewSet

router = DefaultRouter()
router.register(r'', FactureViewSet, basename='facture')

urlpatterns = router.urls