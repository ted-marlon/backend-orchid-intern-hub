from django.core.management.base import BaseCommand
from datetime import date, timedelta
from stagiaires.models import Stagiaire
from presences.utils import (
    alerter_fin_stage_approchante,
    generer_alertes_rapports_manquants
)


class Command(BaseCommand):
    help = 'Vérifie et génère les alertes automatiques quotidiennes'

    def handle(self, *args, **kwargs):
        self.stdout.write(' Vérification des alertes automatiques...')
        
        # 1. Vérifier les rapports manquants
        try:
            generer_alertes_rapports_manquants()
            self.stdout.write(self.style.SUCCESS('✅ Alertes rapports manquants générées'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur rapports manquants: {e}'))
        
        # 2. Vérifier les fins de stage approchantes
        try:
            today = date.today()
            seuil_jours = 5
            seuil_date = today + timedelta(days=seuil_jours)
            
            # Utiliser date_fin au lieu de date_fin_stage
            stagiaires_fin_proche = Stagiaire.objects.filter(
                date_fin__lte=seuil_date,
                date_fin__gte=today
            )
            
            count = 0
            for stagiaire in stagiaires_fin_proche:
                jours_restants = (stagiaire.date_fin - today).days
                alerter_fin_stage_approchante(stagiaire, jours_restants)
                count += 1
            
            self.stdout.write(self.style.SUCCESS(f'✅ {count} alertes fin de stage générées'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur fin de stage: {e}'))
        
        self.stdout.write(self.style.SUCCESS(' Toutes les alertes automatiques ont été vérifiées !'))