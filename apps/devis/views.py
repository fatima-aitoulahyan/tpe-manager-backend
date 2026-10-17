from datetime import date, timedelta
from decimal import Decimal

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import  Devis, LigneDevis
from .serializers import  DevisSerializer, DevisListSerializer
from django.http import FileResponse
from utils.pdf import generer_pdf
from rest_framework.pagination import PageNumberPagination
import os
import json
from ..billing.models import LigneFacture, Facture
from openai import OpenAI
from django.db.models import Q , Value
from ..clients.models import Client
from django.db.models.functions import Concat


class DevisPagination(PageNumberPagination):
    page_size            = 10
    page_size_query_param = 'page_size'
    max_page_size        = 50

class DevisViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class   = DevisPagination

    def get_serializer_class(self):
        if self.action == 'list':
            return DevisListSerializer
        return DevisSerializer

    def get_queryset(self):
        qs = Devis.objects.filter(
            user=self.request.user
        ).select_related('client').prefetch_related('lignes')

        if self.action != 'list':
            return qs

        statut = self.request.query_params.get('statut')
        client = self.request.query_params.get('client')
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')

        if statut:
            qs = qs.filter(statut=statut)
        else:
            qs = qs.exclude(statut='ARCHIVE')

        if client:
            qs = qs.filter(client_id=client)
        if date_debut:
            qs = qs.filter(date_creation__gte=date_debut)
        if date_fin:
            qs = qs.filter(date_creation__lte=date_fin)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # ── POST /api/devis/{id}/change_status/ ──
    @action(detail=True, methods=['post'], url_path='change_status')
    def changer_statut(self, request, pk=None):
        devis          = self.get_object()
        nouveau_statut = request.data.get('status')
        statuts_valides = [s.value for s in Devis.StatutDevis]

        if nouveau_statut not in statuts_valides:
            return Response(
                {'error': f'Invalid status. Choose from: {statuts_valides}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if devis.statut == Devis.StatutDevis.ACCEPTE:
            return Response(
                {'error': 'An accepted quote cannot change status anymore.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        devis.statut = nouveau_statut
        devis.save()
        return Response({
            'message': f'Status changed to {nouveau_statut}',
            'status': devis.statut
        })

    # ── POST /api/devis/{id}/duplicate/ ──
    @action(detail=True, methods=['post'], url_path='duplicate')
    def dupliquer(self, request, pk=None):
        devis  = self.get_object()
        lignes = list(devis.lignes.all())

        devis.pk     = None
        devis.numero = None
        devis.statut = Devis.StatutDevis.BROUILLON
        devis.save()

        for ligne in lignes:
            ligne.pk    = None
            ligne.devis = devis
            ligne.save()

        return Response(
            DevisSerializer(devis, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    # ── GET /api/devis/stats/ ──
    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs    = Devis.objects.filter(user=request.user)
        total = qs.count()

        by_status = {
            s.value: qs.filter(statut=s.value).count()
            for s in Devis.StatutDevis
        }

        accepted = by_status.get('ACCEPTE', 0)
        rate     = round((accepted / total * 100), 1) if total > 0 else 0

        return Response({
            'total_quotes':      total,
            'by_status':         by_status,
            'conversion_rate':   f"{rate}%",
        })

    # ── GET /api/devis/{id}/pdf/ ──
    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):


        devis = self.get_object()
        path  = generer_pdf('devis/devis_pdf.html', {
            'devis':  devis,
            'lignes': devis.lignes.all(),
        })
        return FileResponse(
            open(path, 'rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"{devis.numero}.pdf"
        )
    @action(detail=True, methods=['post'], url_path='convert_to_facture')
    def convert_to_facture(self, request, pk=None):
        devis = self.get_object()

        if hasattr(devis, 'facture') and devis.facture:
            return Response(
                {'error': 'Ce devis a déjà été converti en facture.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        facture = Facture.objects.create(
            user          = devis.user,
            client        = devis.client,
            devis         = devis,
            taux_tva      = devis.taux_tva,
            mode_paiement = devis.mode_paiement,
            conditions    = devis.conditions,
            statut        = Facture.StatutFacture.BROUILLON,
        )

        for ligne_devis in devis.lignes.all():
            LigneFacture.objects.create(
                facture       = facture,
                libelle       = ligne_devis.libelle,
                prix_unitaire = ligne_devis.prix_unitaire,
                quantite      = ligne_devis.quantite,
            )

        facture.montant_total = facture.calculer_montant_ttc()
        facture.save(update_fields=['montant_total'])

        devis.statut = Devis.StatutDevis.ACCEPTE
        devis.save(update_fields=['statut'])
        return Response(
            {'id': facture.id, 'numero': facture.numero},
            status=status.HTTP_201_CREATED
        )
    @action(detail=False, methods=['post'], url_path='generate-from-text')
    def generate_from_text(self, request):
        texte_brut = request.data.get('text')

        if not texte_brut:
            return Response(
                {'error': 'Le champ "text" est obligatoire.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt_systeme = (
            "Tu es un assistant comptable intelligent. À partir du texte fourni, "
            "extrait les informations pour créer un devis. "
            "Tu dois retourner EXCLUSIVEMENT un objet JSON valide avec cette structure exacte : "
            "{"
            "  \"client_nom\": \"Nom (et prénom si mentionné) du client\","
            "  \"conditions\": \"Conditions de paiement si mentionnées\","
            "  \"lignes\": ["
            "    {"
            "      \"libelle\": \"Description de la prestation ou du produit\","
            "      \"quantite\": 1,"
            "      \"prix_unitaire\": 0.0"
            "    }"
            "  ]"
            "}"
        )

        try:
            response = client_openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt_systeme},
                    {"role": "user", "content": texte_brut}
                ],
                response_format={"type": "json_object"}
            )

            donnees_ia = json.loads(response.choices[0].message.content)
            client_nom = (donnees_ia.get('client_nom') or '').strip()

            if not client_nom:
                return Response(
                    {'error': "Aucun nom de client n'a pu être identifié dans le texte."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ── Recherche du client existant ──
            client_nom_normalise = client_nom.strip()

            clients_qs = Client.objects.filter(user=request.user).annotate(
                nom_complet=Concat('nom', Value(' '), 'prenom'),
                nom_complet_inverse=Concat('prenom', Value(' '), 'nom'),
            )

            client_obj = clients_qs.filter(
                Q(nom_complet__icontains=client_nom_normalise) |
                Q(nom_complet_inverse__icontains=client_nom_normalise) |
                Q(nom__icontains=client_nom_normalise) |
                Q(prenom__icontains=client_nom_normalise) |
                Q(nom_entreprise__icontains=client_nom_normalise)
            ).first()

            if client_obj is None:
                return Response(
                    {
                        'error': f"Le client \"{client_nom}\" n'existe pas dans votre base. "
                                 f"Veuillez l'ajouter avant de générer ce devis.",
                        'client_nom_detecte': client_nom,
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            devis = Devis.objects.create(
                user=request.user,
                client=client_obj,
                conditions=donnees_ia.get('conditions', ''),
                statut=Devis.StatutDevis.BROUILLON,
                mode_paiement=Devis.ModePaiement.VIREMENT,
                date_validite=date.today() + timedelta(days=30),
                taux_tva=Decimal('20'),
            )

            for ligne in donnees_ia.get('lignes', []):
                LigneDevis.objects.create(
                    devis=devis,
                    libelle=ligne.get('libelle'),
                    quantite=ligne.get('quantite', 1),
                    prix_unitaire=ligne.get('prix_unitaire', 0.0)
                )

            serializer = DevisSerializer(devis, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f"Erreur lors du traitement par l'IA : {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


