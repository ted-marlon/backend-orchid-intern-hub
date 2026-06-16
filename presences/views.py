from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import date
from .models import Presence
from .serializers import PresenceSerializer
from .utils import notify_rh_and_stagiaire, is_moroccan_holiday, generate_pointing_qr, verify_qr_data
from stagiaires.models import Stagiaire
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class PresenceViewSet(viewsets.ModelViewSet):
    queryset = Presence.objects.all()
    serializer_class = PresenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'stagiaire':
            return Presence.objects.filter(stagiaire__user=user)
        return Presence.objects.all()

    @action(detail=False, methods=['get'], url_path='get-daily-qrs', permission_classes=[IsAuthenticated])
    def get_daily_qrs(self, request):
        """Récupère les QR codes du jour (Entrée et Sortie)"""
        # Note: En prod, on pourrait limiter cet accès aux admins/RH ou une tablette fixe
        qr_entree = generate_pointing_qr('entree')
        qr_sortie = generate_pointing_qr('sortie')
        return Response({
            "entree": qr_entree,
            "sortie": qr_sortie,
            "date": date.today().isoformat()
        })

    @action(detail=False, methods=['post'], url_path='scanner')
    def scanner(self, request):
        """
        Action appelée quand un stagiaire scanne un QR code via son mobile.
        """
        user = request.user
        if not hasattr(user, 'stagiaire_profile'):
            return Response({"error": "Seuls les stagiaires peuvent pointer."}, status=status.HTTP_403_FORBIDDEN)
        
        qr_data = request.data.get('qr_data')
        if not qr_data:
            return Response({"error": "Données du QR code manquantes."}, status=status.HTTP_400_BAD_REQUEST)
        
        verified = verify_qr_data(qr_data)
        if not verified:
            return Response({"error": "QR Code invalide ou expiré."}, status=status.HTTP_400_BAD_REQUEST)
        
        type_pointage = verified['type']
        qr_date = verified['date']
        
        # Vérification que le QR code est bien pour aujourd'hui
        if qr_date != date.today().isoformat():
            return Response({"error": "Ce QR Code n'est plus valide (date incorrecte)."}, status=status.HTTP_400_BAD_REQUEST)

        stagiaire = user.stagiaire_profile
        now = timezone.now()
        today = now.date()
        current_time = now.time()

        presence, created = Presence.objects.get_or_create(
            stagiaire=stagiaire,
            date=today,
            defaults={'statut': 'present'}
        )

        if type_pointage == 'entree':
            if presence.heure_entree:
                return Response({"message": "Vous avez déjà pointé votre entrée aujourd'hui."}, status=status.HTTP_400_BAD_REQUEST)
            presence.heure_entree = current_time
            presence.statut = 'present'
            msg = f"{user.nom} {user.prenom} a pointé son ARRIVÉE à {current_time.strftime('%H:%M')} le {today.strftime('%d/%m/%Y')}"
        else: # sortie
            if not presence.heure_entree:
                return Response({"error": "Vous devez pointer l'entrée avant la sortie."}, status=status.HTTP_400_BAD_REQUEST)
            if presence.heure_sortie:
                return Response({"message": "Vous avez déjà pointé votre sortie aujourd'hui."}, status=status.HTTP_400_BAD_REQUEST)
            presence.heure_sortie = current_time
            msg = f"{user.nom} {user.prenom} a pointé son DÉPART à {current_time.strftime('%H:%M')} le {today.strftime('%d/%m/%Y')}"

        presence.save()
        notify_rh_and_stagiaire(stagiaire, msg)
        
        return Response({
            "message": "Pointage QR validé avec succès.",
            "type": type_pointage,
            "heure": current_time.strftime('%H:%M')
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='pointer')
    def pointer(self, request):
        user = request.user
        if not hasattr(user, 'stagiaire_profile'):
            return Response({"error": "Seuls les stagiaires peuvent pointer."}, status=status.HTTP_403_FORBIDDEN)
        
        stagiaire = user.stagiaire_profile
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        type_pointage = request.data.get('type') # 'entree' ou 'sortie'
        
        if type_pointage not in ['entree', 'sortie']:
            return Response({"error": "Type de pointage invalide. Attendu: 'entree' ou 'sortie'."}, status=status.HTTP_400_BAD_REQUEST)

        presence, created = Presence.objects.get_or_create(
            stagiaire=stagiaire,
            date=today,
            defaults={'statut': 'present'}
        )

        if type_pointage == 'entree':
            if presence.heure_entree:
                return Response({"message": "Vous avez déjà pointé votre entrée aujourd'hui."}, status=status.HTTP_400_BAD_REQUEST)
            presence.heure_entree = current_time
            presence.statut = 'present'
            msg = f"{user.nom} {user.prenom} a pointé son ARRIVÉE à {current_time.strftime('%H:%M')} le {today.strftime('%d/%m/%Y')}"
        else: # sortie
            if not presence.heure_entree:
                return Response({"error": "Vous devez pointer l'entrée avant la sortie."}, status=status.HTTP_400_BAD_REQUEST)
            if presence.heure_sortie:
                return Response({"message": "Vous avez déjà pointé votre sortie aujourd'hui."}, status=status.HTTP_400_BAD_REQUEST)
            presence.heure_sortie = current_time
            msg = f"{user.nom} {user.prenom} a pointé son DÉPART à {current_time.strftime('%H:%M')} le {today.strftime('%d/%m/%Y')}"

        presence.save()
        
        # Envoi d'alerte WhatsApp (Stagiaire + RH)
        notify_rh_and_stagiaire(stagiaire, msg)
        
        return Response({
            "message": "Pointage enregistré avec succès.",
            "type": type_pointage,
            "heure": current_time.strftime('%H:%M')
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='justifier')
    def justifier(self, request, pk=None):
        presence = self.get_object()
        justification = request.data.get('justification')
        
        if not justification:
            return Response({"error": "La justification est obligatoire."}, status=status.HTTP_400_BAD_REQUEST)
        
        presence.justification = justification
        presence.est_justifiee = True
        presence.statut = 'absent' # On s'assure que c'est bien une absence
        presence.save()
        
        return Response({"message": "Justification enregistrée."}, status=status.HTTP_200_OK)
