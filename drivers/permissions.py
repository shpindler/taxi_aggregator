# drivers/permissions.py
from rest_framework import permissions
from .models import Driver


class IsDriverOwner(permissions.BasePermission):
    """Разрешает доступ только владельцу профиля водителя."""

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


class IsDriver(permissions.BasePermission):
    """Разрешает доступ только пользователям с ролью driver."""

    def has_permission(self, request, view):
        return Driver.objects.filter(user=request.user).exists()
