from django.http import JsonResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from stagiaires.models import Stagiaire
from projets.models import Projet
from rapports.models import RapportJournalier
from presences.models import Presence


def dashboard_stats(request):
    """
    API endpoint pour récupérer les statistiques du tableau de bord administrateur
    """
    today = timezone.now().date()
    current_month = today.replace(day=1)
    
    # 1. STAGIAIRES - Nombre total et nouveaux ce mois
    total_stagiaires = Stagiaire.objects.count()
    new_stagiaires_this_month = Stagiaire.objects.filter(
        user__date_joined__gte=current_month
    ).count()
    
    # 2. ACTIFS AUJOURD'HUI - Pourcentage de stagiaires présents aujourd'hui
    # Utiliser uniquement la table Presence pour calculer les stagiaires actifs
    presences_today = Presence.objects.filter(date=today)
    total_actifs = presences_today.count()
    
    presents_today = 0
    if total_actifs > 0:
        presents_today = presences_today.filter(statut='present').count()
        pourcentage_actifs = round((presents_today / total_actifs) * 100)
    else:
        pourcentage_actifs = 0
    
    message_presence = "Tous présents" if pourcentage_actifs == 100 else f"{total_actifs - presents_today} absent(s)"
    
    # 3. PROJETS EN COURS - Nombre et avancement moyen
    projets_en_cours = Projet.objects.filter(etat='en_cours')
    total_projets = projets_en_cours.count()
    
    if total_projets > 0:
        avancement_moyen = round(projets_en_cours.aggregate(Avg('pourcentage_avancement'))['pourcentage_avancement__avg'] or 0)
    else:
        avancement_moyen = 0
    
    # 4. RAPPORTS DÉPOSÉS - Nombre de rapports du jour et manquants
    rapports_deposes_today = RapportJournalier.objects.filter(
        date_rapport=today,
        depose=True
    ).count()
    
    # Rapports attendus = nombre de stagiaires actifs
    rapports_attendus = total_actifs
    rapports_manquants = max(0, rapports_attendus - rapports_deposes_today)
    
    # 5. ALERTES NON LUES - Basées sur les absences non justifiées et autres critères
    # Alertes: stagiaires avec 2+ absences non justifiées
    alertes_critiques = Stagiaire.objects.filter(
        absences_nj_count__gte=2
    ).count()
    
    # Alertes totales (incluant les critiques)
    alertes_totales = alertes_critiques
    
    stats = {
        'stagiaires': {
            'total': total_stagiaires,
            'new_this_month': new_stagiaires_this_month,
            'message': f"+{new_stagiaires_this_month} ce mois" if new_stagiaires_this_month > 0 else "0 ce mois"
        },
        'actifs_aujourdhui': {
            'pourcentage': pourcentage_actifs,
            'message': message_presence
        },
        'projets_en_cours': {
            'total': total_projets,
            'avancement_moyen': avancement_moyen,
            'message': f"{avancement_moyen}% avancement"
        },
        'rapports_deposes': {
            'total': rapports_deposes_today,
            'manquants': rapports_manquants,
            'message': f"{rapports_manquants} manquant(s)" if rapports_manquants > 0 else "Tous déposés"
        },
        'alertes_non_lues': {
            'total': alertes_totales,
            'critiques': alertes_critiques,
            'message': f"{alertes_critiques} critique(s)" if alertes_critiques > 0 else "Aucune alerte"
        }
    }
    
    return JsonResponse(stats)
