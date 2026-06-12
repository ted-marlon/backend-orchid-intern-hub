from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StagiaireViewSet

router = DefaultRouter()
router.register(r'stagiaires', StagiaireViewSet)

urlpatterns = [
    path('', include(router.urls)),
]