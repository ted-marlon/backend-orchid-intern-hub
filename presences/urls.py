from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PresenceViewSet, 
    AlerteViewSet, 
    JustificationViewSet,
    generer_alertes_manuelles
)

router = DefaultRouter()
router.register(r'presences', PresenceViewSet, basename='presence')
router.register(r'alertes', AlerteViewSet, basename='alerte')
router.register(r'justifications', JustificationViewSet, basename='justification')

urlpatterns = [
    path('', include(router.urls)),
    path('generer-alertes/', generer_alertes_manuelles, name='generer-alertes'),
]
