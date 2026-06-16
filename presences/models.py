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
        super().save(*args, **kwargs)
        if self.statut == 'absent' and not self.est_justifiee:
            blocked = self.stagiaire.update_absences_count()
            if blocked:
                from .utils import send_whatsapp_alert
                msg = f"Compte bloqué — 3 absences non justifiées pour {self.stagiaire.user.nom} {self.stagiaire.user.prenom}"
                send_whatsapp_alert(self.stagiaire.user.telephone_whatsapp, msg)
        elif self.statut == 'absent' and self.est_justifiee:
            self.stagiaire.update_absences_count()
