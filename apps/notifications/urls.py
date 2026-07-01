from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PreferencesNotificationView, NotificationViewSet, register_device_token

router = DefaultRouter()
router.register('list', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('preferences/', PreferencesNotificationView.as_view()),
    path('register-device/', register_device_token),

    path('', include(router.urls)),
]