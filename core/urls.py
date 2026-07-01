from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core import settings

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/', include('apps.users.urls')),
    path('api/devis/', include('apps.devis.urls')),
    path('api/clients/', include('apps.clients.urls')),
    path('api/factures/', include('apps.billing.urls')),
    path('api/tresorerie/', include('apps.cashflow.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/credit/', include('apps.credit.urls')),

    # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)