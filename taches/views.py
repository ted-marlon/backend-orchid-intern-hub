from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Tache
from .serializers import TacheSerializer, TacheCreateUpdateSerializer
from users.permissions import IsAdminOrRH


class TacheViewSet(viewsets.ModelViewSet):
    """
    API CRUD complète pour les tâches :
    - GET /api/taches/ (liste)
    - POST /api/taches/ (créer)
    - GET /api/taches/{id}/ (détail)
    - PUT /api/taches/{id}/ (modifier complètement)
    - PATCH /api/taches/{id}/ (modifier partiellement)
    - DELETE /api/taches/{id}/ (supprimer)
    """
    
    queryset = Tache.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Utiliser des serializers différents selon l'action"""
        if self.action in ['create', 'update', 'partial_update']:
            return TacheCreateUpdateSerializer
        return TacheSerializer
    
    def get_permissions(self):
        """
        Permissions :
        - Admin/RH : créer, modifier, supprimer
        - Tous les utilisateurs authentifiés : lire
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminOrRH]
        return super().get_permissions()
    
    def get_queryset(self):
        """Filtrer par projet si fourni en paramètre"""
        queryset = Tache.objects.all()
        projet_id = self.request.query_params.get('projet_id')
        
        if projet_id:
            queryset = queryset.filter(projet_id=projet_id)
        
        return queryset
    
    @action(detail=True, methods=['patch'])
    def marquer_terminee(self, request, pk=None):
        """
        Marquer une tâche comme terminée
        PATCH /api/taches/{id}/marquer_terminee/
        """
        tache = self.get_object()
        tache.statut = 'terminee'
        tache.realisee = True
        tache.save()
        serializer = self.get_serializer(tache)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def marquer_en_cours(self, request, pk=None):
        """
        Marquer une tâche comme en cours
        PATCH /api/taches/{id}/marquer_en_cours/
        """
        tache = self.get_object()
        tache.statut = 'en_cours'
        tache.realisee = False
        tache.save()
        serializer = self.get_serializer(tache)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_projet(self, request):
        """
        Lister les tâches d'un projet
        GET /api/taches/par_projet/?projet_id=1
        """
        projet_id = request.query_params.get('projet_id')
        
        if not projet_id:
            return Response(
                {'error': 'Le paramètre projet_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        taches = self.get_queryset().filter(projet_id=projet_id)
        serializer = self.get_serializer(taches, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_stagiaire(self, request):
        """
        Lister les tâches assignées à un stagiaire
        GET /api/taches/par_stagiaire/?stagiaire_id=1
        """
        stagiaire_id = request.query_params.get('stagiaire_id')
        
        if not stagiaire_id:
            return Response(
                {'error': 'Le paramètre stagiaire_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        taches = self.queryset.filter(assignee_a_id=stagiaire_id)
        serializer = self.get_serializer(taches, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def terminees(self, request):
        """
        Lister les tâches terminées
        GET /api/taches/terminees/
        """
        taches = self.queryset.filter(statut='terminee')
        serializer = self.get_serializer(taches, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def en_cours(self, request):
        """
        Lister les tâches en cours
        GET /api/taches/en_cours/
        """
        taches = self.queryset.filter(statut='en_cours')
        serializer = self.get_serializer(taches, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def priorite_haute(self, request):
        """
        Lister les tâches de priorité haute
        GET /api/taches/priorite_haute/
        """
        taches = self.queryset.filter(priorite='haute')
        serializer = self.get_serializer(taches, many=True)
        return Response(serializer.data)

# Create your views here.
