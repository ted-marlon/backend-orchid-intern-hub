import logging
from django.core.management.base import BaseCommand
from datetime import date
from stagiaires.models import Stagiaire
from rapports.models import RapportJournalier
from presences.utils import send_whatsapp_alert

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Envoie un rappel WhatsApp à 17h aux stagiaires qui n'ont pas encore déposé leur rapport journalier."

    def handle(self, *args, **options):
        today = date.today()
        self.stdout.write(self.style.WARNING(f"Début du traitement des rappels de rapport journalier pour le {today}"))

        # Récupérer les stagiaires actifs pour qui le stage est en cours
        active_interns = Stagiaire.objects.filter(
            statut='accepte',
            user__is_active=True,
            date_debut__lte=today,
            date_fin__gte=today
        )

        sent_count = 0
        for intern in active_interns:
            # Vérifier si un rapport journalier déposé existe pour aujourd'hui
            has_report = RapportJournalier.objects.filter(
                stagiaire=intern,
                date_rapport=today,
                depose=True
            ).exists()

            if not has_report:
                phone = intern.user.telephone_whatsapp
                if phone:
                    msg = (
                        f"Bonjour {intern.user.prenom}, ceci est un rappel pour déposer "
                        f"votre rapport journalier des tâches d'aujourd'hui ({today.strftime('%d/%m/%Y')}). "
                        f"Veuillez le soumettre depuis votre espace stagiaire."
                    )
                    self.stdout.write(f"Envoi du rappel à {intern.user.prenom} {intern.user.nom} ({phone})...")
                    success = send_whatsapp_alert(phone, msg)
                    if success:
                        sent_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Impossible d'envoyer le rappel à {intern.user.prenom} {intern.user.nom} : "
                            f"numéro WhatsApp manquant."
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Traitement terminé. {sent_count} rappels WhatsApp envoyés."
            )
        )
