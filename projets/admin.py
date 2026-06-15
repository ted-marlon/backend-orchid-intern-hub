from django.contrib import admin
from .models import Projet


class ProjetAdmin(admin.ModelAdmin):
    list_display = ('nom', 'responsable', 'etat', 'pourcentage_avancement', 'date_limite', 'created_at')
    list_filter = ('etat', 'created_at', 'date_limite')
    search_fields = ('nom', 'description', 'responsable__email')
    readonly_fields = ('created_at', 'updated_at', 'etat')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'description', 'responsable')
        }),
        ('Stagiaires', {
            'fields': ('stagiaires',)
        }),
        ('Planification', {
            'fields': ('date_debut', 'date_limite')
        }),
        ('Suivi', {
            'fields': ('etat', 'pourcentage_avancement')
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('stagiaires',)


admin.site.register(Projet, ProjetAdmin)

# Register your models here.
