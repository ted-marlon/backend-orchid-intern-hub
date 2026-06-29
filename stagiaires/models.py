from django.db import models
from django.contrib.auth.models import User
from django.conf import settings 

class Departement(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom



class Stagiaire(models.Model):


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
    departement = models.ForeignKey(
        Departement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stagiaires'
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

    def update_absences_count(self):
        from presences.models import Presence
        from presences.utils import send_whatsapp_alert
        count = Presence.objects.filter(
            stagiaire=self, 
            statut='absent', 
            est_justifiee=False
        ).count()
        self.absences_nj_count = count
        self.save()
        
        if count == 2:
            send_whatsapp_alert(self.user.telephone_whatsapp, "Avertissement : 2 absences non justifiées enregistrées")
        
        if count >= 3:
            self.user.is_active = False
            self.user.save()
            return True
        return False

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
