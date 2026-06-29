# stagiaires/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.utils import timezone
from .models import Stagiaire
from .serializers import StagiaireSerializer, StagiaireUpdateSerializer, UserStagiaireCreateSerializer
from users.permissions import IsAdminOrRH


class StagiaireViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les stagiaires
    """
    queryset = Stagiaire.objects.all()
    serializer_class = StagiaireSerializer
    permission_classes = []
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return StagiaireUpdateSerializer
        return StagiaireSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminOrRH])

    def create_with_user(self, request):
        """
        Créer un nouvel utilisateur ET un stagiaire en une seule requête
        POST /api/stagiaires/create_with_user/
        """
        serializer = UserStagiaireCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            stagiaire = serializer.save()
            return Response(
                {
                    'id': stagiaire.id,
                    'user_id': stagiaire.user.id,
                    'user_email': stagiaire.user.email,
                    'message': 'Stagiaire créé avec succès'
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[])
    def list_for_dashboard(self, request):
        """
        Retourne la liste des stagiaires formatée pour le tableau de bord frontend
        GET /api/stagiaires/list_for_dashboard/
        """
        stagiaires = Stagiaire.objects.select_related('user', 'departement').all()
        
        stagiaires_list = []
        for stagiaire in stagiaires:
            # Déterminer le statut basé sur stage_valide et les dates
            if stagiaire.stage_valide and stagiaire.date_fin and stagiaire.date_fin < timezone.now().date():
                statut = 'Terminé'
            else:
                statut = 'En cours'  # Statut par défaut
            
            # Mapping des rapports
            rapport_map = {
                'en_attente': 'Non déposé',
                'valide': 'Déposé',
                'refuse': 'En relecture',
            }
            rapport = rapport_map.get(stagiaire.rapport_final_statut, 'Non déposé')
            if not stagiaire.rapport_final_depose:
                rapport = 'Non déposé'
            
            # Génération des initiales
            initiale = f"{stagiaire.user.prenom[0] if stagiaire.user.prenom else ''}{stagiaire.user.nom[0] if stagiaire.user.nom else ''}".upper()
            
            # Couleur basée sur le statut
            couleur_map = {
                'Terminé': 'bg-success/20 text-success',
                'En cours': 'bg-warning/15 text-warning ring-warning/25',
            }
            couleur = couleur_map.get(statut, 'bg-primary/20 text-primary')
            
            # Formatage des dates
            stage_debut = stagiaire.date_debut.strftime('%d/%m/%Y') if stagiaire.date_debut else '—'
            stage_fin = stagiaire.date_fin.strftime('%d/%m/%Y') if stagiaire.date_fin else '—'
            
            # Récupérer le nom du département
            departement_nom = stagiaire.departement.nom if stagiaire.departement else 'Non assigné'
            
            stagiaires_list.append({
                'id': str(stagiaire.id),
                'nom': f"{stagiaire.user.prenom} {stagiaire.user.nom}",
                'email': stagiaire.user.email,
                'ecole': stagiaire.ecole,
                'formation': stagiaire.formation,
                'departement': departement_nom,
                'statut': statut,
                'absences': stagiaire.absences_nj_count,
                'absencesMax': 3,
                'stageDebut': stage_debut,
                'stageFin': stage_fin,
                'rapport': rapport,
                'initiale': initiale,
                'couleur': couleur,
            })
        
        return JsonResponse({'stagiaires': stagiaires_list})





# Create your views here.
