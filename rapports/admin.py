from django.contrib import admin
from .models import RapportJournalier, RapportFinal

@admin.register(RapportJournalier)
class RapportJournalierAdmin(admin.ModelAdmin):
    list_display = ('stagiaire', 'date_rapport', 'depose', 'created_at')
    list_filter = ('depose', 'date_rapport', 'stagiaire')
    search_fields = ('stagiaire__user__nom', 'stagiaire__user__prenom', 'commentaire')
    ordering = ('-date_rapport',)

@admin.register(RapportFinal)
class RapportFinalAdmin(admin.ModelAdmin):
    list_display = ('stagiaire', 'statut_validation', 'date_depot', 'valide_par')
    list_filter = ('statut_validation', 'date_depot')
    search_fields = ('stagiaire__user__nom', 'stagiaire__user__prenom', 'commentaire_rh')
    ordering = ('-date_depot',)
