from rest_framework import serializers
from .models import Presence

class PresenceSerializer(serializers.ModelSerializer):
    nom_stagiaire = serializers.CharField(source='stagiaire.user.nom', read_only=True)
    prenom_stagiaire = serializers.CharField(source='stagiaire.user.prenom', read_only=True)
    departement = serializers.CharField(
        source='stagiaire.departement.nom',
        read_only=True,
        default='—'
    )

    class Meta:
        model = Presence
        fields = [
            'id', 'stagiaire', 'nom_stagiaire', 'prenom_stagiaire',
            'departement', 'date', 'heure_entree', 'heure_sortie',
            'statut', 'justification', 'est_justifiee'
        ]
        read_only_fields = ['id', 'date', 'heure_entree', 'heure_sortie']
