from rest_framework import serializers
from .models import Presence
from .models import Alerte, Justification

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

from .models import Alerte, Justification

class AlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerte
        fields = [
            'id', 'titre', 'description', 'severite', 'statut',
            'source', 'date_creation', 'date_resolution'
        ]
        read_only_fields = ['date_creation', 'date_resolution']


class JustificationSerializer(serializers.ModelSerializer):
    nom_stagiaire = serializers.SerializerMethodField()
    
    class Meta:
        model = Justification
        fields = [
            'id', 'stagiaire', 'nom_stagiaire', 'type', 'date',
            'motif', 'statut', 'date_demande', 'date_traitement',
            'traite_par'
        ]
        read_only_fields = ['date_demande', 'date_traitement', 'traite_par']
    
    def get_nom_stagiaire(self, obj):
        return f"{obj.stagiaire.user.prenom} {obj.stagiaire.user.nom}"
