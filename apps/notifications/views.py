from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import PreferencesNotification, DeviceToken
from .serializers import PreferencesNotificationSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import NotificationInApp
from .serializers import NotificationInAppSerializer

class PreferencesNotificationView(generics.RetrieveUpdateAPIView):
    """
    GET /api/notifications/preferences/
    PUT /api/notifications/preferences/
    """
    serializer_class   = PreferencesNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        prefs, _ = PreferencesNotification.objects.get_or_create(
            user=self.request.user
        )
        return prefs




class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = NotificationInAppSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationInApp.objects.filter(
            user=self.request.user)

    @action(detail=True, methods=['post'])
    def marquer_lue(self, request, pk=None):
        notif = self.get_object()
        notif.lue = True
        notif.save()
        return Response({'message': 'Notification marquée comme lue.'})

    @action(detail=False, methods=['post'])
    def marquer_toutes_lues(self, request):
        self.get_queryset().filter(lue=False).update(lue=True)
        return Response({'message': 'Toutes les notifications marquées comme lues.'})

    @action(detail=False, methods=['get'])
    def non_lues_count(self, request):
        count = self.get_queryset().filter(lue=False).count()
        return Response({'count': count})

    @action(detail=False, methods=['post'])
    def supprimer_groupee(self, request):
        ids = request.data.get('ids', [])

        if not ids:
            return Response(
                {'error': 'Aucun identifiant fourni.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        notifications_a_supprimer = self.get_queryset().filter(id__in=ids)
        count = notifications_a_supprimer.count()
        notifications_a_supprimer.delete()

        return Response(
            {'message': f'{count} notification(s) supprimée(s) avec succès.'},
            status=status.HTTP_200_OK
        )
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device_token(request):
    token    = request.data.get('token')
    platform = request.data.get('platform', 'android')
    if not token:
        return Response({'error': 'Token requis'}, status=400)
    DeviceToken.objects.update_or_create(
        token=token,
        defaults={'user': request.user, 'platform': platform}
    )
    return Response({'status': 'ok'})