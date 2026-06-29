from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from datetime import date, timedelta
from io import StringIO

from users.models import CustomUser
from stagiaires.models import Stagiaire
from projets.models import Projet
from taches.models import Tache
from rapports.models import RapportJournalier, RapportFinal

class RapportsTestCase(TestCase):
    def setUp(self):
        # 1. Création des utilisateurs
        self.rh_user = CustomUser.objects.create_user(
            email='rh@example.com',
            nom='RH',
            prenom='Responsable',
            role='rh',
            password='password123',
            telephone_whatsapp='+212600000001'
        )
        self.stagiaire_user = CustomUser.objects.create_user(
            email='stagiaire@example.com',
            nom='Stagiaire',
            prenom='Jean',
            role='stagiaire',
            password='password123',
            telephone_whatsapp='+212600000002'
        )

        # 2. Création du profil Stagiaire
        self.stagiaire = Stagiaire.objects.create(
            user=self.stagiaire_user,
            ecole='ENSA',
            formation='Génie Informatique',
            telephone='0600000002',
            date_debut=date.today() - timedelta(days=5),
            date_fin=date.today() + timedelta(days=25),
            statut='accepte'
        )

        # 3. Création d'un projet et de tâches
        self.projet = Projet.objects.create(
            nom='Projet Test',
            description='Description du projet test',
            responsable=self.rh_user,
            date_debut=date.today() - timedelta(days=5),
            date_limite=date.today() + timedelta(days=25)
        )
        self.projet.stagiaires.add(self.stagiaire)

        # Tâche en cours
        self.tache_en_cours = Tache.objects.create(
            projet=self.projet,
            assignee_a=self.stagiaire,
            nom='Tâche en cours 1',
            description='Détails',
            statut='en_cours',
            date_limite=date.today() + timedelta(days=2)
        )

        # Tâche terminée aujourd'hui
        self.tache_terminee = Tache.objects.create(
            projet=self.projet,
            assignee_a=self.stagiaire,
            nom='Tâche terminée 1',
            description='Détails',
            statut='terminee',
            date_limite=date.today() + timedelta(days=2)
        )

    def test_rapport_journalier_auto_population(self):
        """
        Teste le peuplement automatique des tâches complétées et en cours dans le rapport journalier.
        """
        rapport = RapportJournalier.objects.create(
            stagiaire=self.stagiaire,
            date_rapport=date.today(),
            commentaire="Travail du jour."
        )
        
        # Appeler le peuplement automatique
        rapport.populate_tasks()
        rapport.save()

        # Vérifier que les tâches sont présentes dans les JSONs
        self.assertEqual(len(rapport.taches_realisees), 1)
        self.assertEqual(rapport.taches_realisees[0]['nom'], 'Tâche terminée 1')

        self.assertEqual(len(rapport.taches_en_cours), 1)
        self.assertEqual(rapport.taches_en_cours[0]['nom'], 'Tâche en cours 1')

    def test_rapport_final_creation_and_sync(self):
        """
        Teste que le dépôt d'un rapport final met à jour les champs du stagiaire.
        """
        # Création du rapport final
        rapport_final = RapportFinal.objects.create(
            stagiaire=self.stagiaire,
            fichier_path='rapports_finaux/test_rapport.pdf',
            statut_validation='en_attente'
        )

        # Recharger le profil stagiaire
        self.stagiaire.refresh_from_db()
        self.assertTrue(self.stagiaire.rapport_final_depose)
        self.assertEqual(self.stagiaire.rapport_final_statut, 'en_attente')

        # Modification du statut vers validé
        rapport_final.statut_validation = 'valide'
        rapport_final.valide_par = self.rh_user
        rapport_final.commentaire_rh = "Excellent travail !"
        rapport_final.save()

        # Vérifier la mise à jour
        self.stagiaire.refresh_from_db()
        self.assertEqual(self.stagiaire.rapport_final_statut, 'valide')
        self.assertTrue(self.stagiaire.stage_valide)

    def test_remind_daily_reports_command(self):
        """
        Teste que la commande remind_daily_reports cible bien les stagiaires actifs sans rapports journaliers.
        """
        out = StringIO()
        call_command('remind_daily_reports', stdout=out)
        output = out.getvalue()
        
        # Doit contenir l'envoi du rappel
        self.assertIn("Envoi du rappel à Jean Stagiaire", output)
        self.assertIn("1 rappels WhatsApp envoyés", output)

        # Créer le rapport et le marquer déposé
        RapportJournalier.objects.create(
            stagiaire=self.stagiaire,
            date_rapport=date.today(),
            depose=True
        )

        # Re-run de la commande
        out2 = StringIO()
        call_command('remind_daily_reports', stdout=out2)
        output2 = out2.getvalue()

        # Aucun rappel ne doit être envoyé cette fois
        self.assertIn("0 rappels WhatsApp envoyés", output2)
        self.assertNotIn("Envoi du rappel à Jean Stagiaire", output2)
