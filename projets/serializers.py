from rest_framework import serializers
from .models import Projet
from stagiaires.serializers import StagiaireSerializer


class ProjetSerializer(serializers.ModelSerializer):
    """Serializer complet pour lire les projets"""
    
    responsable_email = serializers.EmailField(
        source='responsable.email',
        read_only=True
    )
    responsable_nom = serializers.CharField(
        source='responsable.get_full_name',
        read_only=True
    )
    stagiaires_details = StagiaireSerializer(
        source='stagiaires',
        many=True,
        read_only=True
    )
    etat_affichage = serializers.CharField(
        source='get_etat_display',
        read_only=True
    )
    jours_restants = serializers.SerializerMethodField()
    
    class Meta:
        model = Projet
        fields = (
            'id', 'nom', 'description', 'responsable', 'responsable_email',
            'responsable_nom', 'stagiaires', 'stagiaires_details', 'date_debut',
            'date_limite', 'etat', 'etat_affichage', 'pourcentage_avancement',
            'jours_restants', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at', 'etat', 'pourcentage_avancement')
    
    def get_jours_restants(self, obj):
        """Calculer les jours restants avant l'échéance"""
        from django.utils import timezone
        delta = obj.date_limite - timezone.now().date()
        return delta.days


class ProjetCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/modifier les projets"""
    
    stagiaires_ids = serializers.PrimaryKeyRelatedField(
        queryset=__import__('stagiaires.models', fromlist=['Stagiaire']).Stagiaire.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Projet
        fields = (
            'nom', 'description', 'responsable', 'date_debut',
            'date_limite', 'stagiaires_ids', 'pourcentage_avancement'
        )
    
    def create(self, validated_data):
        stagiaires_ids = validated_data.pop('stagiaires_ids', [])
        projet = Projet.objects.create(**validated_data)
        
        if stagiaires_ids:
            projet.stagiaires.set(stagiaires_ids)
        
        return projet
    
    def update(self, instance, validated_data):
        stagiaires_ids = validated_data.pop('stagiaires_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if stagiaires_ids is not None:
            instance.stagiaires.set(stagiaires_ids)
        
        return instance