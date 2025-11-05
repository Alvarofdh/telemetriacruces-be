"""
Permisos personalizados para el sistema de roles
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permiso para verificar si el usuario es Administrador
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.profile
            return profile.is_admin()
        except:
            return False


class IsAdminOrMaintenance(permissions.BasePermission):
    """
    Permiso para verificar si el usuario es Administrador o Personal de Mantenimiento
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.profile
            return profile.is_admin() or profile.is_maintenance()
        except:
            return False


class IsObserverOrAbove(permissions.BasePermission):
    """
    Permiso para verificar si el usuario es Observador o superior
    (Todos los usuarios autenticados pueden ver)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Solo verificar que tenga perfil
        try:
            profile = request.user.profile
            return True
        except:
            return False


class CanModifyCruces(permissions.BasePermission):
    """
    Permiso para modificar cruces (solo Administrador)
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            # Todos los usuarios autenticados pueden ver
            return request.user.is_authenticated and hasattr(request.user, 'profile')
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.profile
            return profile.is_admin()  # Solo admin puede modificar
        except:
            return False


class CanModifyAlertas(permissions.BasePermission):
    """
    Permiso para modificar alertas (solo Administrador puede resolver)
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            # Todos los usuarios autenticados pueden ver
            return request.user.is_authenticated and hasattr(request.user, 'profile')
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.profile
            return profile.is_admin()  # Solo admin puede modificar
        except:
            return False

