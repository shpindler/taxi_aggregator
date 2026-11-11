from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Trip, TripStatus
from .serializers import TripReadSerializer, TripWriteSerializer
from .permissions import IsDriverOrPassenger
from drivers.models import Driver
from passengers.models import Passenger


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.select_related(
        "driver__user", "passenger__user"
    ).all()

    permission_classes = [permissions.IsAuthenticated, IsDriverOrPassenger]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "driver", "passenger"]
    ordering_fields = ["created_at", "price"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TripWriteSerializer
        return TripReadSerializer

    def get_queryset(self):
        """Водитель видит свои поездки, пассажир — свои, staff — все."""
        qs = super().get_queryset()
        user = self.request.user

        if user.is_staff:
            return qs

        # Пытаемся определить роль пользователя
        driver = Driver.objects.filter(user=user).first()
        passenger = Passenger.objects.filter(user=user).first()

        if driver:
            return qs.filter(driver=driver)
        if passenger:
            return qs.filter(passenger=passenger)
        return qs.none()

    def perform_create(self, serializer):
        """Если создаёт пассажир — автоматически привязываем его профиль."""
        user = self.request.user
        passenger = Passenger.objects.filter(user=user).first()

        if passenger and not serializer.validated_data.get("passenger"):
            serializer.save(passenger=passenger)
        else:
            serializer.save()

    # ---------- Кастомные actions ----------

    @action(detail=True, methods=["post"], url_path="accept")
    def accept(self, request, pk=None):
        """Водитель принимает поездку."""
        trip = self.get_object()

        if trip.status != TripStatus.SEARCHING:
            return Response(
                {"detail": "Trip is not in SEARCHING status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        driver = Driver.objects.filter(user=request.user).first()
        if not driver:
            return Response(
                {"detail": "You are not a driver"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not driver.is_available:
            return Response(
                {"detail": "Driver is not available"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        trip.driver = driver
        trip.status = TripStatus.ACCEPTED
        trip.save(update_fields=["driver", "status", "updated_at"])
        driver.is_available = False
        driver.save(update_fields=["is_available"])

        return Response(TripReadSerializer(trip).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """Отмена поездки (пассажиром или водителем)."""
        trip = self.get_object()

        if trip.status in (TripStatus.COMPLETED, TripStatus.CANCELLED):
            return Response(
                {"detail": "Trip cannot be cancelled in current status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        trip.status = TripStatus.CANCELLED
        trip.save(update_fields=["status", "updated_at"])

        if trip.driver:
            trip.driver.is_available = True
            trip.driver.save(update_fields=["is_available"])

        return Response(TripReadSerializer(trip).data)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        """Завершение поездки водителем."""
        trip = self.get_object()

        if not trip.driver or trip.driver.user_id != request.user.id:
            return Response(
                {"detail": "Only the assigned driver can complete the trip"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if trip.status not in (TripStatus.ACCEPTED, TripStatus.IN_PROGRESS):
            return Response(
                {"detail": "Trip cannot be completed in current status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        trip.status = TripStatus.COMPLETED
        trip.save(update_fields=["status", "updated_at"])

        trip.driver.is_available = True
        trip.driver.save(update_fields=["is_available"])

        return Response(TripReadSerializer(trip).data)