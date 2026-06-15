from rest_framework import serializers
from .models import Tache
from stagiaires.serializers import StagiaireSerializer


class TacheSerializer(serializers.ModelSerializer):
    """Serializer complet pour lire les tâches"""
    
    stagiaire_nom = serializers.CharField(
        source='assignee_a.user.get_full_name',
        read_only=True
    )
    projet_nom = serializers.CharField(
        source='projet.nom',
        read_only=True
    )
    priorite_affichage = serializers.CharField(
        source='get_priorite_display',
        read_only=True
    )
    statut_affichage = serializers.CharField(
        source='get_statut_display',
        read_only=True
    )
    jours_restants = serializers.SerializerMethodField()
    
    class Meta:
        model = Tache
        fields = (
            'id', 'projet', 'projet_nom', 'nom', 'description',
            'realisee', 'assignee_a', 'stagiaire_nom', 'priorite',
            'priorite_affichage', 'date_limite', 'statut', 'statut_affichage',
            'jours_restants', 'date_creation', 'date_modification'
        )
        read_only_fields = ('date_creation', 'date_modification')
    
    def get_jours_restants(self, obj):
        """Calculer les jours restants"""
        from django.utils import timezone
        delta = obj.date_limite - timezone.now().date()
        return delta.days


class TacheCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/modifier les tâches"""
    
    class Meta:
        model = Tache
        fields = (
            'projet', 'nom', 'description', 'assignee_a',
            'priorite', 'date_limite', 'statut', 'realisee'
        )
    
    def validate(self, attrs):
        """Synchroniser realisee et statut"""
        if attrs.get('realisee'):
            attrs['statut'] = 'terminee'
        return attrs