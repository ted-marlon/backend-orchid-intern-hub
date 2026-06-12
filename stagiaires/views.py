# stagiaires/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Stagiaire
from .serializers import StagiaireSerializer, UserStagiaireCreateSerializer
from users.permissions import IsAdminOrRH


class StagiaireViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les stagiaires
    """
    queryset = Stagiaire.objects.all()
    serializer_class = StagiaireSerializer
    permission_classes = [IsAuthenticated]
    
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





# Create your views here.
