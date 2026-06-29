from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from datetime import date

from .models import RapportJournalier, RapportFinal
from .serializers import RapportJournalierSerializer, RapportFinalSerializer
from users.permissions import IsAdminOrRH
from stagiaires.models import Stagiaire

class RapportJournalierViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les rapports journaliers.
    """
    serializer_class = RapportJournalierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return RapportJournalier.objects.none()
        
        # Filtrer selon le rôle
        if user.role == 'stagiaire':
            # Un stagiaire ne voit que ses propres rapports
            return RapportJournalier.objects.filter(stagiaire__user=user)
        elif user.role in ['admin', 'rh', 'manager']:
            # Les managers, RH et admin voient tout
            queryset = RapportJournalier.objects.all()
            # Possibilité de filtrer par stagiaire ou par date via query parameters
            stagiaire_id = self.request.query_params.get('stagiaire_id')
            date_rapport = self.request.query_params.get('date_rapport')
            if stagiaire_id:
                queryset = queryset.filter(stagiaire_id=stagiaire_id)
            if date_rapport:
                queryset = queryset.filter(date_rapport=date_rapport)
            return queryset
        return RapportJournalier.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'stagiaire':
            # Récupérer automatiquement le profil stagiaire de l'utilisateur connecté
            try:
                stagiaire = user.stagiaire_profile
            except Stagiaire.DoesNotExist:
                raise ValidationError("Profil stagiaire introuvable pour cet utilisateur.")
            
            # Vérifier si un rapport existe déjà pour aujourd'hui
            date_rapport = serializer.validated_data.get('date_rapport', date.today())
            if RapportJournalier.objects.filter(stagiaire=stagiaire, date_rapport=date_rapport).exists():
                raise ValidationError(f"Un rapport journalier a déjà été créé pour le {date_rapport}.")
                
            serializer.save(stagiaire=stagiaire)
        else:
            # Pour Admin/RH/Manager, ils doivent spécifier le stagiaire
            if 'stagiaire' not in serializer.validated_data:
                raise ValidationError("Le champ 'stagiaire' est requis pour les utilisateurs non-stagiaires.")
            serializer.save()

    @action(detail=False, methods=['post'], url_path='deposer')
    def deposer_rapport_aujourdhui(self, request):
        """
        Permet au stagiaire connecté de générer et de déposer (soumettre) son rapport pour aujourd'hui.
        """
        user = request.user
        if user.role != 'stagiaire':
            return Response(
                {"detail": "Seuls les stagiaires peuvent déposer un rapport journalier."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            stagiaire = user.stagiaire_profile
        except Stagiaire.DoesNotExist:
            return Response(
                {"detail": "Profil stagiaire introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        today = date.today()
        commentaire = request.data.get('commentaire', '')

        # Récupérer ou créer le rapport journalier pour aujourd'hui
        rapport, created = RapportJournalier.objects.get_or_create(
            stagiaire=stagiaire,
            date_rapport=today,
            defaults={'depose': True, 'commentaire': commentaire}
        )

        # Si le rapport existait déjà mais n'était pas déposé, ou pour rafraîchir les tâches
        rapport.populate_tasks()
        if commentaire:
            rapport.commentaire = commentaire
        
        rapport.depose = True
        rapport.save()

        serializer = self.get_serializer(rapport)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RapportFinalViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer le rapport final de stage.
    """
    serializer_class = RapportFinalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return RapportFinal.objects.none()

        if user.role == 'stagiaire':
            return RapportFinal.objects.filter(stagiaire__user=user)
        elif user.role in ['admin', 'rh', 'manager']:
            queryset = RapportFinal.objects.all()
            stagiaire_id = self.request.query_params.get('stagiaire_id')
            if stagiaire_id:
                queryset = queryset.filter(stagiaire_id=stagiaire_id)
            return queryset
        return RapportFinal.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'stagiaire':
            try:
                stagiaire = user.stagiaire_profile
            except Stagiaire.DoesNotExist:
                raise ValidationError("Profil stagiaire introuvable.")

            # Vérifier si un rapport final existe déjà pour ce stagiaire
            if RapportFinal.objects.filter(stagiaire=stagiaire).exists():
                raise ValidationError("Vous avez déjà déposé un rapport final.")

            # Un stagiaire ne peut pas définir le statut de validation ou le validateur
            serializer.save(
                stagiaire=stagiaire,
                statut_validation='en_attente',
                valide_par=None,
                commentaire_rh=None
            )
        else:
            # Pour Admin/RH
            if 'stagiaire' not in serializer.validated_data:
                raise ValidationError("Le champ 'stagiaire' est requis.")
            serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if user.role == 'stagiaire':
            # Un stagiaire ne peut modifier que le fichier de son rapport final (s'il n'est pas encore validé)
            instance = self.get_object()
            if instance.statut_validation == 'valide':
                raise ValidationError("Impossible de modifier un rapport final déjà validé.")
            
            # Forcer les champs RH à ne pas changer
            serializer.save(
                statut_validation='en_attente',
                valide_par=None,
                commentaire_rh=None
            )
        else:
            # Pour RH/Admin
            serializer.save()

    @action(detail=True, methods=['post'], url_path='valider', permission_classes=[permissions.IsAuthenticated, IsAdminOrRH])
    def valider_rapport(self, request, pk=None):
        """
        Permet à un RH ou Admin de valider ou refuser le rapport final d'un stagiaire.
        """
        rapport = self.get_object()
        statut = request.data.get('statut_validation')
        commentaire = request.data.get('commentaire_rh', '')

        if statut not in ['valide', 'refuse', 'en_attente']:
            return Response(
                {"detail": "Statut de validation invalide. Choisissez parmi: valide, refuse, en_attente."},
                status=status.HTTP_400_BAD_REQUEST
            )

        rapport.statut_validation = statut
        rapport.commentaire_rh = commentaire
        rapport.valide_par = request.user
        rapport.save()

        serializer = self.get_serializer(rapport)
        return Response(serializer.data, status=status.HTTP_200_OK)
