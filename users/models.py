from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager personnalisé pour CustomUser avec email comme USERNAME_FIELD"""
    
    def create_user(self, email, nom, prenom, password=None, role='stagiaire', **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, nom=nom, prenom=prenom, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, nom, prenom, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, nom, prenom, password=password, **extra_fields)


# ⚠️ Vérifie bien que c'est "CustomUser" et pas "Customuser" ou "customuser"
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('rh', 'RH'),
        ('manager', 'Manager'),
        ('stagiaire', 'Stagiaire'),
    )

    username = None 
    email = models.EmailField(unique=True, max_length=150)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='stagiaire')
    telephone_whatsapp = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom', 'role']
    
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.role})"
# Create your models here.
