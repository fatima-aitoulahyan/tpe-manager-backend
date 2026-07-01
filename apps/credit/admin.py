from django.contrib import admin
from django.utils.html import format_html
from .models import DemandeFinancement, Justificatif, OffreFinancement

class JustificatifInline(admin.TabularInline):
    model    = Justificatif
    extra    = 0
    readonly_fields = ['uploaded_at']


class OffreFinancementInline(admin.TabularInline):
    model = OffreFinancement
    extra = 1   # permet d'ajouter facilement une offre


@admin.register(DemandeFinancement)
class DemandeFinancementAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'user', 'type_financement',
        'montant_demande', 'duree_mois',
        'statut_colore', 'niveau_badge',
        'date_demande',
    ]
    list_filter   = ['statut', 'type_financement', 'niveau_eligibilite']
    search_fields = ['user__email', 'user__nom', 'objet_financement']
    inlines       = [JustificatifInline, OffreFinancementInline]

    readonly_fields = [
        'user', 'score_eligibilite', 'niveau_eligibilite',
        'date_demande', 'date_consentement', 'consentement_cndp',
    ]

    fieldsets = (
        ('Infos', {
            'fields': ('user',)
        }),
        ('Demande', {
            'fields': (
                'type_financement',
                'montant_demande',
                'duree_mois',
                'objet_financement'
            )
        }),
        ('Décision', {
            'fields': ('statut', 'motif_refus')
        }),
    )

    def statut_colore(self, obj):
        colors = {
            'SOUMISE':           '#6b7280',
            'EN_ANALYSE':         '#f59e0b',
            'FAVORABLE':          '#10b981',
            'DEFAVORABLE':        '#ef4444',
            'DOSSIER_INCOMPLET':  '#f97316',
        }
        color = colors.get(obj.statut, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:12px; font-size:11px;">{}</span>',
            color, obj.get_statut_display()
        )
    statut_colore.short_description = 'Statut'

    def niveau_badge(self, obj):
        colors = {'VERT': '#10b981', 'ORANGE': '#f59e0b', 'ROUGE': '#ef4444'}
        color = colors.get(obj.niveau_eligibilite, '#6b7280')
        return format_html(
            '<span style="color:{}; font-weight:bold;">● {}</span>',
            color, obj.niveau_eligibilite or '-'
        )
    niveau_badge.short_description = 'Éligibilité'
    actions = ['marquer_en_analyse']

    def marquer_en_analyse(self, request, queryset):
        demandes = queryset.filter(statut='SOUMISE')
        count = 0
        for demande in demandes:
            demande.statut = 'EN_ANALYSE'
            demande.save()
            count += 1

        self.message_user(request, f"{count} demande(s) passée(s) en analyse.")
    marquer_en_analyse.short_description = "Marquer comme 'En cours d'analyse'"

@admin.register(OffreFinancement)
class OffreFinancementAdmin(admin.ModelAdmin):
    list_display  = ['demande', 'partenaire_nom', 'taux_interet',
                     'duree_mois', 'mensualite_estimee']
    search_fields = ['partenaire_nom']