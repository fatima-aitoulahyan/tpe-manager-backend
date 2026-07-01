from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Count
from apps.billing.models import Facture


def calculer_score_eligibilite(user):
    """
    Calcule un score de pré-éligibilité (0-100) basé sur :
    - Volume de facturation (40 pts)
    - Ancienneté du compte (30 pts)
    - Régularité des encaissements (30 pts)
    """

    score   = Decimal('0')
    conseils = []
    six_mois = date.today() - timedelta(days=180)
    volume = Facture.objects.filter(
        user=user,
        date_emission__gte=six_mois,
        statut='PAYEE'
    ).aggregate(total=Sum('montant_total'))['total'] or Decimal('0')

    if volume >= 50000:
        score += 40
    elif volume >= 20000:
        score += 25
        conseils.append("Augmentez votre volume de facturation pour améliorer votre score.")
    elif volume >= 5000:
        score += 10
        conseils.append("Votre volume de facturation est encore faible.")
    else:
        conseils.append("Commencez à facturer régulièrement pour construire votre historique.")

    anciennete_jours = (date.today() - user.created_at.date()).days
    if anciennete_jours >= 365:
        score += 30
    elif anciennete_jours >= 180:
        score += 20
    elif anciennete_jours >= 90:
        score += 10
        conseils.append("Votre compte est encore récent. L'ancienneté améliore l'éligibilité.")
    else:
        conseils.append("Continuez à utiliser l'application pour augmenter votre ancienneté.")
    factures_en_attente = Facture.objects.filter(
        user=user,
        statut__in=['EN_ATTENTE', 'PARTIELLEMENT_PAYEE']
    ).count()

    factures_payees = Facture.objects.filter(
        user=user, statut='PAYEE'
    ).count()

    total_factures = factures_en_attente + factures_payees

    if total_factures > 0:
        taux_regularite = (factures_payees / total_factures) * 100
        if taux_regularite >= 80:
            score += 30
        elif taux_regularite >= 50:
            score += 15
            conseils.append("Régularisez vos factures en attente pour améliorer votre score.")
        else:
            conseils.append("Trop de factures impayées. Régularisez-les en priorité.")
    else:
        conseils.append("Émettez et encaissez des factures pour évaluer votre régularité.")

    if not user.statut_fiscal:
        conseils.append("Complétez votre profil fiscal pour améliorer votre éligibilité.")

    score = min(score, Decimal('100'))

    if score >= 70:
        niveau = 'VERT'
    elif score >= 40:
        niveau = 'ORANGE'
    else:
        niveau = 'ROUGE'

    return {
        'score':   float(score),
        'niveau':  niveau,
        'conseils': conseils,
    }