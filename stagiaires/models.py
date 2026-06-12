from django.db import models
from django.contrib.auth.models import User
from django.conf import settings 


class Stagiaire(models.Model):

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),
    ]

    RAPPORT_STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('refuse', 'Refusé'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='stagiaire_profile' # Pratique pour faire user.stagiaire_profile
    )

    ecole = models.CharField(max_length=200)
    formation = models.CharField(max_length=200)
    telephone = models.CharField(max_length=20)

    cv_path = models.FileField(
        upload_to='cv/',
        blank=True,
        null=True
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente'
    )

    date_debut = models.DateField()
    date_fin = models.DateField()

    convention_validee = models.BooleanField(default=False)

    stage_valide = models.BooleanField(default=False)

    absences_nj_count = models.IntegerField(default=0)

    rapport_final_depose = models.BooleanField(default=False)

    rapport_final_statut = models.CharField(
        max_length=20,
        choices=RAPPORT_STATUT_CHOICES,
        default='en_attente'
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
