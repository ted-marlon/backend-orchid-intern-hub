from django.db import models
from django.conf import settings
from projets.models import Projet
from stagiaires.models import Stagiaire


class Tache(models.Model):
    """Modèle pour gérer les tâches d'un projet"""
    
    PRIORITE_CHOICES = [
        ('haute', 'Haute'),
        ('moyenne', 'Moyenne'),
        ('faible', 'Faible'),
    ]
    
    STATUT_CHOICES = [
        ('a_faire', 'À faire'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
    ]
    
    # Relations
    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        related_name='taches',
        help_text="Projet parent de la tâche"
    )
    
    assignee_a = models.ForeignKey(
        Stagiaire,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taches',
        help_text="Stagiaire assigné à la tâche"
    )
    
    # Champs de base
    nom = models.CharField(
        max_length=255,
        help_text="Nom/Libellé descriptif de la tâche"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description détaillée de la tâche"
    )
    
    # État
    realisee = models.BooleanField(
        default=False,
        help_text="La tâche est-elle réalisée ?"
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='a_faire',
        help_text="Statut actuel de la tâche"
    )
    
    priorite = models.CharField(
        max_length=20,
        choices=PRIORITE_CHOICES,
        default='moyenne',
        help_text="Priorité de la tâche"
    )
    
    # Dates
    date_limite = models.DateField(
        help_text="Échéance de réalisation"
    )
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_limite', '-priorite']
        verbose_name = 'Tâche'
        verbose_name_plural = 'Tâches'
        indexes = [
            models.Index(fields=['projet', 'statut']),
            models.Index(fields=['assignee_a', 'statut']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.get_statut_display()})"
    
    def save(self, *args, **kwargs):
       """
       Synchroniser realisee et statut avant sauvegarde
       """
    # Si le statut est "terminee", forcer realisee = True
       if self.statut == 'terminee':
          self.realisee = True
    
    # Si le statut n'est pas "terminee", forcer realisee = False
       elif self.statut in ['a_faire', 'en_cours']:
            self.realisee = False
    
    # Si realisee est changé à True (via case à cocher), statut devient "terminee"
       if self.realisee and self.statut != 'terminee':
          self.statut = 'terminee'
    
       super().save(*args, **kwargs)
    
    # Recalculer l'avancement du projet parent
       self.projet.recalculer_avancement()
    
    def delete(self, *args, **kwargs):
        """Recalculer l'avancement du projet après suppression"""
        projet = self.projet
        super().delete(*args, **kwargs)
        projet.recalculer_avancement()

# Create your models here.
