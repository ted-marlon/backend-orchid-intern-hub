from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RapportJournalierViewSet, RapportFinalViewSet

router = DefaultRouter()
router.register(r'journaliers', RapportJournalierViewSet, basename='rapport-journalier')
router.register(r'finaux', RapportFinalViewSet, basename='rapport-final')

urlpatterns = [
    path('rapports/', include(router.urls)),
]
