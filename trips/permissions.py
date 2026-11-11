# trips/permissions.py
from rest_framework import permissions


class IsPassenger(permissions.BasePermission):
    """Только пользователи с ролью passenger."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "passenger"
        )


class IsDriver(permissions.BasePermission):
    """Только пользователи с ролью driver."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "driver"
        )


class IsTripParticipant(permissions.BasePermission):
    """Доступ к объекту только пассажиру или водителю этой поездки."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True
        if hasattr(obj, "passenger") and obj.passenger.user_id == user.id:
            return True
        if hasattr(obj, "driver") and obj.driver.user_id == user.id:
            return True
        return False
    

class IsDriverOrPassenger(permissions.BasePermission):
    """Доступ только участникам поездки или staff."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if request.method in permissions.SAFE_METHODS:
            return (
                hasattr(obj, "driver") and obj.driver.user_id == request.user.id
            ) or (
                hasattr(obj, "passenger") and obj.passenger.user_id == request.user.id
            )
        # Изменять может только пассажир (или staff)
        return obj.passenger and obj.passenger.user_id == request.user.id