from rest_framework import permissions
from .models import Passenger


class IsPassengerOwner(permissions.BasePermission):
    """Разрешает доступ только владельцу профиля пассажира."""

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


class IsPassenger(permissions.BasePermission):
    """Разрешает доступ только пользователям с ролью passenger."""

    def has_permission(self, request, view):
        return Passenger.objects.filter(user=request.user).exists()
