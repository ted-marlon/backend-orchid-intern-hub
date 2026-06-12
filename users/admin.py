from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'nom', 'prenom', 'role', 'telephone_whatsapp', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('email', 'nom', 'prenom')
    ordering = ('-created_at',)

    # Champs affichés lors de la création/modification
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'prenom', 'telephone_whatsapp', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nom', 'prenom', 'role', 'telephone_whatsapp', 'password1', 'password2'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
# Register your models here.
