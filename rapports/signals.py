from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import date
from .models import RapportJournalier
from stagiaires.models import Stagiaire
from presences.utils import alerter_rapport_manquant

@receiver(post_save, sender=Stagiaire)
def verifier_rapports_manquants(sender, instance, **kwargs):
    """
    Vérifie chaque jour si les stagiaires ont déposé leurs rapports
    Note: Ce signal peut être déclenché par une tâche cron ou manuellement
    """
    pass  # On va utiliser une tâche cron à la place

def generer_alertes_rapports_manquants():
    """
    Fonction à appeler chaque jour (via cron) pour générer les alertes de rapports manquants
    """
    today = date.today()
    
    # Récupérer tous les stagiaires actifs
    stagiaires = Stagiaire.objects.filter(actif=True)
    
    for stagiaire in stagiaires:
        # Vérifier si le stagiaire a déposé son rapport aujourd'hui
        rapport_existe = RapportJournalier.objects.filter(
            stagiaire=stagiaire,
            date_rapport=today,
            depose=True
        ).exists()
        
        if not rapport_existe:
            alerter_rapport_manquant(stagiaire, today)