from django.db import models
from django.conf import settings
from stagiaires.models import Stagiaire

class Presence(models.Model):
    STATUT_CHOICES = [
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('ferie', 'Jour Férié'),
    ]

    stagiaire = models.ForeignKey(Stagiaire, on_delete=models.CASCADE, related_name='presences')
    date = models.DateField()
    heure_entree = models.TimeField(null=True, blank=True)
    heure_sortie = models.TimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='present')
    
    justification = models.TextField(blank=True, null=True)
    est_justifiee = models.BooleanField(default=False)

    class Meta:
        unique_together = ('stagiaire', 'date')
        verbose_name = "Présence"
        verbose_name_plural = "Présences"

    def __str__(self):
        return f"{self.stagiaire.user.nom} {self.stagiaire.user.prenom} - {self.date} ({self.get_statut_display()})"

    def save(self, *args, **kwargs):
        # Vérifier si c'est une nouvelle présence ou une mise à jour
        is_new = self._state.adding
        
        super().save(*args, **kwargs)
        
        # Alerter sur les absences non justifiées
        if self.statut == 'absent' and not self.est_justifiee:
            # Vérifier si c'est une nouvelle absence ou si elle vient d'être marquée non justifiée
            if is_new or not hasattr(self, '_was_justified') or self._was_justified:
                alerter_absence_non_justifiee(self.stagiaire, self.date)
            
            # Logique existante pour bloquer le compte
            blocked = self.stagiaire.update_absences_count()
            if blocked:
                from .utils import send_whatsapp_alert
                msg = f"Compte bloqué — 3 absences non justifiées pour {self.stagiaire.user.nom} {self.stagiaire.user.prenom}"
                send_whatsapp_alert(self.stagiaire.user.telephone_whatsapp, msg)
        
        # Alerter sur les retards de pointage (entrée après 9h)
        if self.heure_entree and self.statut == 'present':
            from datetime import time
            heure_limite = time(9, 0)
            if self.heure_entree > heure_limite:
                # Vérifier si c'est un nouveau pointage d'entrée
                if is_new or not hasattr(self, '_had_entree'):
                    alerter_retard_pointage(self.stagiaire, self.heure_entree, self.date)

class Alerte(models.Model):
    SEVERITE_CHOICES = [
        ('critique', 'Critique'),
        ('avertissement', 'Avertissement'),
        ('info', 'Info'),
    ]
    
    STATUT_CHOICES = [
        ('non-lue', 'Non lue'),
        ('lue', 'Lue'),
        ('resolue', 'Résolue'),
    ]
    
    titre = models.CharField(max_length=200)
    description = models.TextField()
    severite = models.CharField(max_length=20, choices=SEVERITE_CHOICES, default='info')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='non-lue')
    source = models.CharField(max_length=100, blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_resolution = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Alerte"
        verbose_name_plural = "Alertes"
    
    def __str__(self):
        return f"[{self.get_severite_display()}] {self.titre}"


class Justification(models.Model):
    TYPE_CHOICES = [
        ('absence', 'Absence'),
        ('retard', 'Retard'),
        ('conge', 'Congé'),
    ]
    
    STATUT_CHOICES = [
        ('en-attente', 'En attente'),
        ('acceptee', 'Acceptée'),
        ('rejetee', 'Rejetée'),
    ]
    
    stagiaire = models.ForeignKey(Stagiaire, on_delete=models.CASCADE, related_name='justifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date = models.DateField()
    motif = models.TextField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en-attente')
    date_demande = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    traite_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='justifications_traitees'
    )
    
    class Meta:
        ordering = ['-date_demande']
        verbose_name = "Justification"
        verbose_name_plural = "Justifications"
    
    def __str__(self):
        return f"{self.stagiaire} - {self.get_type_display()} ({self.get_statut_display()})"
