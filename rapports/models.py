from django.db import models
from django.conf import settings
from datetime import date
from stagiaires.models import Stagiaire
from presences.utils import send_whatsapp_alert
from cloudinary.models import CloudinaryField

class RapportJournalier(models.Model):
    """
    Modèle pour le rapport journalier des tâches du stagiaire.
    Chaque stagiaire dépose un rapport par jour (automatique ou manuel).
    """
    date_rapport = models.DateField(default=date.today)
    stagiaire = models.ForeignKey(
        Stagiaire,
        on_delete=models.CASCADE,
        related_name='rapports_journaliers'
    )
    taches_realisees = models.JSONField(
        blank=True,
        null=True,
        help_text="Liste JSON des tâches terminées aujourd'hui"
    )
    taches_en_cours = models.JSONField(
        blank=True,
        null=True,
        help_text="Liste JSON des tâches non terminées"
    )
    commentaire = models.TextField(
        blank=True,
        null=True,
        help_text="Commentaire libre du stagiaire"
    )
    depose = models.BooleanField(
        default=False,
        help_text="Indique si le rapport a été soumis"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_rapport']
        unique_together = ('stagiaire', 'date_rapport')
        verbose_name = "Rapport journalier"
        verbose_name_plural = "Rapports journaliers"

    def __str__(self):
        return f"Rapport Journalier - {self.stagiaire.user.prenom} {self.stagiaire.user.nom} - {self.date_rapport}"

    def populate_tasks(self):
        """
        Remplit automatiquement les tâches terminées aujourd'hui et les tâches en cours
        si elles ne sont pas fournies.
        """
        from taches.models import Tache
        
        # Tâches terminées aujourd'hui (date de modification = date_rapport)
        completed_tasks = Tache.objects.filter(
            assignee_a=self.stagiaire,
            statut='terminee',
            date_modification__date=self.date_rapport
        )
        
        # Tâches en cours (statut != terminee)
        in_progress_tasks = Tache.objects.filter(
            assignee_a=self.stagiaire
        ).exclude(statut='terminee')

        self.taches_realisees = [
            {
                "id": t.id,
                "nom": t.nom,
                "description": t.description,
                "projet": t.projet.nom if t.projet else None
            }
            for t in completed_tasks
        ]
        
        self.taches_en_cours = [
            {
                "id": t.id,
                "nom": t.nom,
                "description": t.description,
                "projet": t.projet.nom if t.projet else None
            }
            for t in in_progress_tasks
        ]


class RapportFinal(models.Model):
    """
    Modèle pour le rapport final de stage déposé par le stagiaire (format PDF).
    """
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('refuse', 'Refusé'),
    ]

    stagiaire = models.OneToOneField(
        Stagiaire,
        on_delete=models.CASCADE,
        related_name='rapport_final'
    )
    fichier = CloudinaryField(
        'fichier', 
        folder='rapports_finaux/',       # Dossier dans Cloudinary
        resource_type='raw',             # OBLIGATOIRE pour les PDF
        blank=True, 
        null=True
    )
    date_depot = models.DateField(auto_now_add=True)
    statut_validation = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente'
    )
    commentaire_rh = models.TextField(
        blank=True,
        null=True,
        help_text="Commentaire de validation ou refus par les RH"
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rapports_finaux_valides',
        help_text="RH ou Admin ayant validé le rapport"
    )

    class Meta:
        verbose_name = "Rapport final de stage"
        verbose_name_plural = "Rapports finaux de stage"

    def __str__(self):
        return f"Rapport Final - {self.stagiaire.user.prenom} {self.stagiaire.user.nom}"

    def save(self, *args, **kwargs):
        # Déterminer si le statut de validation a changé pour envoyer une alerte
        is_new = self.pk is None
        old_status = None
        if not is_new:
            old_instance = RapportFinal.objects.get(pk=self.pk)
            old_status = old_instance.statut_validation

        super().save(*args, **kwargs)

        # Mettre à jour la fiche du stagiaire
        stagiaire = self.stagiaire
        stagiaire.rapport_final_depose = True
        stagiaire.rapport_final_statut = self.statut_validation
        
        # Si validé, on peut mettre à jour stage_valide si c'est la règle (facultatif mais propre)
        if self.statut_validation == 'valide':
            stagiaire.stage_valide = True
        elif self.statut_validation == 'refuse':
            stagiaire.stage_valide = False
            
        stagiaire.save()

        # Envoi d'une alerte WhatsApp si le statut a changé vers validé ou refusé
        if not is_new and old_status != self.statut_validation:
            if self.statut_validation in ['valide', 'refuse']:
                status_label = "validé" if self.statut_validation == 'valide' else "refusé"
                msg = f"Bonjour {stagiaire.user.prenom}, votre rapport final de stage a été {status_label} par l'administration."
                if self.commentaire_rh:
                    msg += f" Commentaire : {self.commentaire_rh}"
                send_whatsapp_alert(stagiaire.user.telephone_whatsapp, msg)
