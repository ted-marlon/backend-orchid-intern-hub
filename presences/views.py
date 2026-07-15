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
from datetime import time
from .models import Alerte, Justification
from .serializers import AlerteSerializer, JustificationSerializer
from django.utils import timezone

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
        from .utils import signer
        from datetime import date
        
        today = date.today().isoformat()
        
        # Générer les données signées pour entrée et sortie
        data_entree = f"pointage:entree:{today}"
        data_sortie = f"pointage:sortie:{today}"
        
        signed_entree = signer.sign(data_entree)
        signed_sortie = signer.sign(data_sortie)
        
        # Générer les QR codes images
        qr_entree = generate_pointing_qr('entree')
        qr_sortie = generate_pointing_qr('sortie')
        
        return Response({
            "entree": qr_entree,
            "sortie": qr_sortie,
            "entree_data": signed_entree,
            "sortie_data": signed_sortie,
            "date": today
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
    
    @action(
        detail=False,
        methods=["get"],
        url_path="dashboard",
        permission_classes=[]
    )
    def dashboard(self, request):
        """
        Retourne les statistiques du dashboard ainsi que la liste des présences.
        """

        today = timezone.localdate()

        presences = (
            Presence.objects
            .filter(date=today)
            .select_related(
                "stagiaire",
                "stagiaire__user",
                "stagiaire__departement"
            )
        )

        serializer = PresenceSerializer(presences, many=True)

        # Statistiques
        presents = presences.filter(statut="present").count()

        absents = presences.filter(statut="absent").count()

        sortis = presences.exclude(
            heure_sortie__isnull=True
        ).count()

        entrees = presences.exclude(
            heure_entree__isnull=True
        ).count()

        # Heure limite d'arrivée (09:00)
        heure_limite = time(9, 0)

        retards_queryset = presences.filter(
            heure_entree__gt=heure_limite
        )

        retards = retards_queryset.count()

        total_retard = 0

        for presence in retards_queryset:
            minutes = (
                presence.heure_entree.hour * 60
                + presence.heure_entree.minute
            ) - (9 * 60)

            total_retard += minutes

        retard_moyen = (
            round(total_retard / retards)
            if retards > 0
            else 0
        )

        total = presences.count()

        taux_presence = (
            round((presents / total) * 100)
            if total > 0
            else 0
        )

        return Response({
            "kpis": {
                "presents": presents,
                "absents": absents,
                "entrees": entrees,
                "sortis": sortis,
                "retards": retards,
                "retard_moyen": retard_moyen,
                "taux_presence": taux_presence,
            },
            "presences": serializer.data
        })
class AlerteViewSet(viewsets.ModelViewSet):
    queryset = Alerte.objects.all()
    serializer_class = AlerteSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'], url_path='resoudre')
    def resoudre(self, request, pk=None):
        alerte = self.get_object()
        alerte.statut = 'resolue'
        alerte.date_resolution = timezone.now()
        alerte.save()
        return Response({"message": "Alerte marquée comme résolue."})
    
    @action(detail=True, methods=['post'], url_path='marquer-lue')
    def marquer_lue(self, request, pk=None):
        alerte = self.get_object()
        if alerte.statut == 'non-lue':
            alerte.statut = 'lue'
            alerte.save()
        return Response({"message": "Alerte marquée comme lue."})


class JustificationViewSet(viewsets.ModelViewSet):
    serializer_class = JustificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'stagiaire':
            return Justification.objects.filter(stagiaire__user=user)
        return Justification.objects.all()
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'stagiaire':
            try:
                stagiaire = user.stagiaire_profile
            except Stagiaire.DoesNotExist:
                raise ValidationError("Profil stagiaire introuvable.")
            serializer.save(stagiaire=stagiaire)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'], url_path='accepter', permission_classes=[IsAuthenticated, IsAdminUser])
    def accepter(self, request, pk=None):
        justification = self.get_object()
        commentaire = request.data.get('commentaire_rh', '')
        
        justification.statut = 'acceptee'
        justification.date_traitement = timezone.now()
        justification.traite_par = request.user
        justification.save()
        
        # Mettre à jour la présence associée si elle existe
        try:
            presence = Presence.objects.get(
                stagiaire=justification.stagiaire,
                date=justification.date
            )
            presence.est_justifiee = True
            presence.justification = justification.motif
            presence.save()
        except Presence.DoesNotExist:
            pass
        
        return Response({"message": "Justification acceptée."})
    
    @action(detail=True, methods=['post'], url_path='rejeter', permission_classes=[IsAuthenticated, IsAdminUser])
    def rejeter(self, request, pk=None):
        justification = self.get_object()
        commentaire = request.data.get('commentaire_rh', '')
        
        justification.statut = 'rejetee'
        justification.date_traitement = timezone.now()
        justification.traite_par = request.user
        justification.save()
        
        return Response({"message": "Justification rejetée."})

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.management import call_command
from io import StringIO
from users.permissions import IsAdminOrRH

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrRH])
def generer_alertes_manuelles(request):
    """
    Endpoint pour déclencher manuellement la génération des alertes
    Accessible uniquement aux Admin et RH
    """
    out = StringIO()
    try:
        call_command('check_alertes', stdout=out)
        return Response({
            'success': True,
            'message': 'Alertes générées avec succès',
            'output': out.getvalue()
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erreur lors de la génération: {str(e)}'
        }, status=500)
