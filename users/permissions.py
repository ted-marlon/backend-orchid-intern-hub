# users/permissions.py
from rest_framework import permissions

class IsAdminOrRH(permissions.BasePermission):
    """
    Autorise l'accès uniquement aux Admins et aux RH.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['admin', 'rh']
        )

class IsAdminOnly(permissions.BasePermission):
    """
    Autorise l'accès uniquement aux Admins.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'admin'
        )