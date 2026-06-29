from rest_framework import serializers
from .models import RapportJournalier, RapportFinal
from stagiaires.models import Stagiaire

class RapportJournalierSerializer(serializers.ModelSerializer):
    nom_stagiaire = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RapportJournalier
        fields = [
            'id',
            'date_rapport',
            'stagiaire',
            'nom_stagiaire',
            'taches_realisees',
            'taches_en_cours',
            'commentaire',
            'depose',
            'created_at'
        ]
        read_only_fields = ['created_at']

    def get_nom_stagiaire(self, obj):
        return f"{obj.stagiaire.user.prenom} {obj.stagiaire.user.nom}"

    def create(self, validated_data):
        instance = RapportJournalier(**validated_data)
        # Si les tâches ne sont pas fournies, on les peuple automatiquement
        if not instance.taches_realisees or not instance.taches_en_cours:
            instance.populate_tasks()
        instance.save()
        return instance


class RapportFinalSerializer(serializers.ModelSerializer):
    nom_stagiaire = serializers.SerializerMethodField(read_only=True)
    nom_valide_par = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RapportFinal
        fields = [
            'id',
            'stagiaire',
            'nom_stagiaire',
            'fichier_path',
            'date_depot',
            'statut_validation',
            'commentaire_rh',
            'valide_par',
            'nom_valide_par'
        ]
        read_only_fields = ['date_depot', 'stagiaire','statut_validation', 'commentaire_rh', 'valide_par']

    def get_nom_stagiaire(self, obj):
        return f"{obj.stagiaire.user.prenom} {obj.stagiaire.user.nom}"

    def get_nom_valide_par(self, obj):
        if obj.valide_par:
            return f"{obj.valide_par.prenom} {obj.valide_par.nom}"
        return None
