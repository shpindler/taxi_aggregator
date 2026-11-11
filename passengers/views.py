# passengers/views.py
from rest_framework import viewsets, status, permissions, mixins
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Passenger
from .permissions import IsPassengerOwner
from .serializers import (
    PassengerReadSerializer,
    PassengerWriteSerializer,
    PassengerLocationSerializer,
    PassengerLoginSerializer,
)


class PassengerViewSet(viewsets.ModelViewSet):
    """
    list:     GET  /api/passengers/                 — только для админов (см. get_queryset)
    retrieve: GET  /api/passengers/{id}/
    create:   POST /api/passengers/                 — создать профиль себе
    update:   PUT  /api/passengers/{id}/
    partial:  PATCH /api/passengers/{id}/
    delete:   DELETE /api/passengers/{id}/
    """
    permission_classes = [IsAuthenticated, IsPassengerOwner]

    def get_queryset(self):
        user = self.request.user
        # админ видит всех, остальные — только себя
        if user.is_superuser:
            return Passenger.objects.select_related("user").all()
        return Passenger.objects.select_related("user").filter(user=user)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PassengerWriteSerializer
        return PassengerReadSerializer

    def get_permissions(self):
        # создавать профиль может любой
        if self.action == "create":
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        passenger = serializer.save()
        out = PassengerReadSerializer(passenger, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["get", "patch"],
        url_path="me",
        serializer_class=PassengerWriteSerializer,
    )
    def me(self, request):
        """GET/PATCH /api/passengers/me/ — профиль текущего пассажира."""
        try:
            passenger = request.user.passenger
        except Passenger.DoesNotExist:
            return Response(
                {"detail": "Passenger profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == "PATCH":
            serializer = PassengerWriteSerializer(
                passenger, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        return Response(PassengerReadSerializer(passenger).data)

    @action(
        detail=False,
        methods=["patch"],
        url_path="me/location",
        serializer_class=PassengerLocationSerializer,
    )
    def update_location(self, request):
        """PATCH /api/passengers/me/location/ — быстрое обновление координат."""
        try:
            passenger = request.user.passenger
        except Passenger.DoesNotExist:
            return Response(
                {"detail": "Passenger profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = PassengerLocationSerializer(
            passenger, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PassengerLoginViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = PassengerLoginSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "role": "passenger",
        }, status=status.HTTP_200_OK)