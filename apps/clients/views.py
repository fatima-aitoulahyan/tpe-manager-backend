from django.shortcuts import render
from rest_framework import viewsets, status
from apps.clients.models import Client
from apps.clients.serializers import ClientSerializer
from rest_framework.permissions import IsAuthenticated

class ClientViewSet(viewsets.ModelViewSet):
    serializer_class   = ClientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)