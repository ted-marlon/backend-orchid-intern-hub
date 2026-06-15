from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Projet
from .serializers import ProjetSerializer, ProjetCreateUpdateSerializer
from users.permissions import IsAdminOrRH


class ProjetViewSet(viewsets.ModelViewSet):
    """
    API CRUD complète pour les projets
    """
    
    queryset = Projet.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Utiliser des serializers différents selon l'action"""
        if self.action in ['create', 'update', 'partial_update']:
            return ProjetCreateUpdateSerializer
        return ProjetSerializer
    
    def get_permissions(self):
        """
        Permissions :
        - Admin/RH : créer, modifier, supprimer
        - Tous les utilisateurs authentifiés : lire
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminOrRH]
        return super().get_permissions()
    
    @action(detail=True, methods=['post'])
    def ajouter_stagiaires(self, request, pk=None):
        """
        Ajouter des stagiaires à un projet
        POST /api/projets/{id}/ajouter_stagiaires/
        Body: {"stagiaires_ids": [1, 2, 3]}
        """
        projet = self.get_object()
        stagiaires_ids = request.data.get('stagiaires_ids', [])
        
        if not stagiaires_ids:
            return Response(
                {'error': 'Vous devez fournir au moins un ID de stagiaire'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        projet.stagiaires.add(*stagiaires_ids)
        serializer = self.get_serializer(projet)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def retirer_stagiaires(self, request, pk=None):
        """
        Retirer des stagiaires d'un projet
        POST /api/projets/{id}/retirer_stagiaires/
        Body: {"stagiaires_ids": [1, 2]}
        """
        projet = self.get_object()
        stagiaires_ids = request.data.get('stagiaires_ids', [])
        
        if not stagiaires_ids:
            return Response(
                {'error': 'Vous devez fournir au moins un ID de stagiaire'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        projet.stagiaires.remove(*stagiaires_ids)
        serializer = self.get_serializer(projet)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def mettre_a_jour_avancement(self, request, pk=None):
        """
        Mettre à jour le pourcentage d'avancement
        PATCH /api/projets/{id}/mettre_a_jour_avancement/
        Body: {"pourcentage_avancement": 50}
        """
        projet = self.get_object()
        pourcentage = request.data.get('pourcentage_avancement')
        
        if pourcentage is None:
            return Response(
                {'error': 'Vous devez fournir un pourcentage'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not (0 <= pourcentage <= 100):
            return Response(
                {'error': 'Le pourcentage doit être entre 0 et 100'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        projet.pourcentage_avancement = pourcentage
        projet.save()
        serializer = self.get_serializer(projet)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def marquer_termine(self, request, pk=None):
        """
        Marquer un projet comme terminé
        PATCH /api/projets/{id}/marquer_termine/
        """
        projet = self.get_object()
        projet.etat = 'termine'
        projet.pourcentage_avancement = 100
        projet.save()
        serializer = self.get_serializer(projet)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def en_cours(self, request):
        """
        Lister les projets en cours
        GET /api/projets/en_cours/
        """
        projets = self.queryset.filter(etat='en_cours')
        serializer = self.get_serializer(projets, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def termines(self, request):
        """
        Lister les projets terminés
        GET /api/projets/termines/
        """
        projets = self.queryset.filter(etat='termine')
        serializer = self.get_serializer(projets, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def en_retard(self, request):
        """
        Lister les projets en retard
        GET /api/projets/en_retard/
        """
        projets = self.queryset.filter(etat='en_retard')
        serializer = self.get_serializer(projets, many=True)
        return Response(serializer.data)

# Create your views here.
