from django.contrib import admin
from .models import Tache


class TacheAdmin(admin.ModelAdmin):
    list_display = ('nom', 'projet', 'assignee_a', 'priorite', 'statut', 'realisee', 'date_limite')
    list_filter = ('statut', 'priorite', 'realisee', 'projet', 'date_limite')
    search_fields = ('nom', 'description', 'projet__nom', 'assignee_a__user__email')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('projet', 'nom', 'description')
        }),
        ('Assignation', {
            'fields': ('assignee_a',)
        }),
        ('État', {
            'fields': ('statut', 'realisee', 'priorite')
        }),
        ('Dates', {
            'fields': ('date_limite', 'date_creation', 'date_modification')
        }),
    )


admin.site.register(Tache, TacheAdmin)
