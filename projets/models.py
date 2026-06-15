from django.db import models
from django.conf import settings
from django.utils import timezone
from stagiaires.models import Stagiaire


class Projet(models.Model):
    """Modèle pour gérer les projets des stagiaires"""
    
    ETAT_CHOICES = [
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('en_retard', 'En retard'),
    ]
    
    # Champs de base
    nom = models.CharField(
        max_length=200,
        help_text="Nom du projet"
    )
    
    description = models.TextField(
        help_text="Description détaillée du projet"
    )
    
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projets_responsable',
        help_text="Responsable du projet (généralement RH ou Manager)"
    )
    
    # Stagiaires assignés
    stagiaires = models.ManyToManyField(
        Stagiaire,
        related_name='projets',
        blank=True,
        help_text="Stagiaires assignés au projet"
    )
    
    # Dates
    date_debut = models.DateField(
        help_text="Date de démarrage du projet"
    )
    
    date_limite = models.DateField(
        help_text="Échéance du projet"
    )
    
    # État et avancement
    etat = models.CharField(
        max_length=20,
        choices=ETAT_CHOICES,
        default='en_cours',
        help_text="État actuel du projet"
    )
    
    pourcentage_avancement = models.IntegerField(
        default=0,
        help_text="Pourcentage d'avancement calculé automatiquement"
    )
    
    # Dates système
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Projet'
        verbose_name_plural = 'Projets'
    
    def __str__(self):
        return f"{self.nom} ({self.get_etat_display()})"
    
    def save(self, *args, **kwargs):
        """
        Mettre à jour l'état du projet avant la sauvegarde
        """
        # Si la date limite est dépassée et le projet n'est pas terminé
        if self.date_limite < timezone.now().date() and self.etat != 'termine':
            self.etat = 'en_retard'
        
        super().save(*args, **kwargs)
    
    def calculer_avancement(self):
        """
        Calculer l'avancement du projet basé sur les tâches
        (À implémenter quand on aura l'app Tâches)
        """
        # Pour l'instant, retourner la valeur sauvegardée
        return self.pourcentage_avancement
    def recalculer_avancement(self):
       """
       Calculer et mettre à jour l'avancement du projet basé sur les tâches
       """
       taches_totales = self.taches.count()
    
       if taches_totales == 0:
            self.pourcentage_avancement = 0
       else:
            taches_terminees = self.taches.filter(statut='terminee').count()
            self.pourcentage_avancement = round((taches_terminees / taches_totales) * 100)
    
    # Mettre à jour l'état si avancement est 100%
       if self.pourcentage_avancement == 100:
           self.etat = 'termine'
    
       self.save(update_fields=['pourcentage_avancement', 'etat'])


