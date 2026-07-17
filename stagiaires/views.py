# stagiaires/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from .models import Stagiaire
from .serializers import StagiaireSerializer, StagiaireUpdateSerializer, UserStagiaireCreateSerializer
from users.permissions import IsAdminOrRH
from presences.models import Presence
from projets.models import Projet
from taches.models import Tache
from rapports.models import RapportJournalier


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
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def stagiaire_dashboard_stats(self, request):
        """
        Retourne les statistiques du dashboard pour le stagiaire connecté
        GET /api/stagiaires/stagiaire_dashboard_stats/
        """
        user = request.user
        if not hasattr(user, 'stagiaire_profile'):
            return Response({"error": "Seuls les stagiaires peuvent accéder à ces statistiques."}, status=status.HTTP_403_FORBIDDEN)
        
        stagiaire = user.stagiaire_profile
        
        # Statistiques de base
        projets_count = Projet.objects.filter(stagiaires=stagiaire).count()
        taches_count = Tache.objects.filter(stagiaire=stagiaire).count()
        rapports_count = RapportJournalier.objects.filter(stagiaire=stagiaire).count()
        
        # Pointages ce mois
        from datetime import datetime
        now = timezone.now()
        current_month = now.month
        current_year = now.year
        pointages_count = Presence.objects.filter(
            stagiaire=stagiaire,
            date__month=current_month,
            date__year=current_year
        ).count()
        
        # Activités récentes
        recent_activities = []
        recent_taches = Tache.objects.filter(stagiaire=stagiaire).order_by('-date_creation')[:3]
        for tache in recent_taches:
            recent_activities.append(f"Tâche: {tache.titre}")
        
        recent_rapports = RapportJournalier.objects.filter(stagiaire=stagiaire).order_by('-date_rapport')[:2]
        for rapport in recent_rapports:
            recent_activities.append(f"Rapport du {rapport.date_rapport}")
        
        # Prochaines échéances
        deadlines = []
        upcoming_taches = Tache.objects.filter(
            stagiaire=stagiaire,
            date_echeance__gte=timezone.now().date()
        ).order_by('date_echeance')[:3]
        for tache in upcoming_taches:
            deadlines.append(f"{tache.titre} - {tache.date_echeance.strftime('%d/%m/%Y')}")
        
        return Response({
            'projets': projets_count,
            'taches': taches_count,
            'rapports': rapports_count,
            'pointages': pointages_count,
            'recent_activities': recent_activities,
            'deadlines': deadlines
        })





# Create your views here.
