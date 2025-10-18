# permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrSuperUserRole(BasePermission):
    """
    POST, PUT, PATCH, DELETE доступны только пользователям с ролями 'Admin' или 'SuperUser'.
    GET, HEAD, OPTIONS доступны всем.
    """
    def has_permission(self, request, view):
        # GET и другие безопасные методы разрешены всем
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Проверяем роль пользователя
        if user.role and user.role.role_name in ['SuperUser', 'Admin']:
            return True

        return False
