# stagiaires/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from .models import Stagiaire

User = get_user_model()

class StagiaireSerializer(serializers.ModelSerializer):
    """Serializer simple pour lire les stagiaires"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_nom = serializers.CharField(source='user.nom', read_only=True)
    user_prenom = serializers.CharField(source='user.prenom', read_only=True)
    
    class Meta:
        model = Stagiaire
        fields = '__all__'


class UserStagiaireCreateSerializer(serializers.Serializer):
    """Serializer pour créer un utilisateur ET un stagiaire ensemble"""
    
    # Champs de l'User
    email = serializers.EmailField()
    prenom = serializers.CharField(max_length=100)
    nom = serializers.CharField(max_length=100)
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    telephone_whatsapp = serializers.CharField(max_length=20, required=False)
    
    # Champs du Stagiaire
    ecole = serializers.CharField(max_length=200)
    formation = serializers.CharField(max_length=200)
    telephone = serializers.CharField(max_length=20)
    date_debut = serializers.DateField()
    date_fin = serializers.DateField()
    cv_path = serializers.FileField(required=False, allow_null=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs
    
    def create(self, validated_data):
        # Séparer les données User et Stagiaire
        user_data = {
            'email': validated_data.pop('email'),
            'prenom': validated_data.pop('prenom'),
            'nom': validated_data.pop('nom'),
            'password': validated_data.pop('password'),
            'telephone_whatsapp': validated_data.pop('telephone_whatsapp', ''),
            'role': 'stagiaire'
        }
        validated_data.pop('password_confirm')  # Supprimer la confirmation
        
        # Créer l'User
        user = User.objects.create(
            email=user_data['email'],
            prenom=user_data['prenom'],
            nom=user_data['nom'],
            telephone_whatsapp=user_data['telephone_whatsapp'],
            role=user_data['role']
        )
        user.set_password(user_data['password'])
        user.save()
        
        # Créer le Stagiaire lié à l'User
        stagiaire = Stagiaire.objects.create(
            user=user,
            **validated_data
        )
        
        return stagiaire
