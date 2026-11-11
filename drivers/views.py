# drivers/views.py
from rest_framework import viewsets, status, permissions, mixins
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Driver
from .permissions import IsDriverOwner
from .serializers import (
    DriverReadSerializer,
    DriverWriteSerializer,
    DriverLocationSerializer,
    DriverLoginSerializer,
)


class DriverViewSet(viewsets.ModelViewSet):
    """
    list:     GET  /api/drivers/                 — только для админов (см. get_queryset)
    retrieve: GET  /api/drivers/{id}/
    create:   POST /api/drivers/                 — создать профиль себе
    update:   PUT  /api/drivers/{id}/
    partial:  PATCH /api/drivers/{id}/
    delete:   DELETE /api/drivers/{id}/
    """
    permission_classes = [IsAuthenticated, IsDriverOwner]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        # админ видит всех, остальные — только себя
        if user.is_superuser:
            return Driver.objects.select_related("user").all()
        return Driver.objects.select_related("user").filter(user=user)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return DriverWriteSerializer
        return DriverReadSerializer

    def get_permissions(self):
        # создавать профиль может любой
        if self.action == "create":
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        driver = serializer.save()
        out = DriverReadSerializer(driver, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["get", "patch"],
        url_path="me",
        serializer_class=DriverLocationSerializer,
    )
    def me(self, request):
        """GET/PATCH /api/drivers/me/ — профиль текущего водителя."""
        try:
            driver = request.user.driver
        except Driver.DoesNotExist:
            return Response(
                {"detail": "Driver profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == "PATCH":
            serializer = DriverLocationSerializer(
                driver, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        return Response(DriverReadSerializer(driver).data)

    @action(
        detail=False,
        methods=["patch"],
        url_path="me/location",
        serializer_class=DriverLocationSerializer,
    )
    def update_location(self, request):
        """PATCH /api/drivers/me/location/ — быстрое обновление координат."""
        try:
            driver = request.user.driver
        except Driver.DoesNotExist:
            return Response(
                {"detail": "Driver profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DriverLocationSerializer(
            driver, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DriverLoginViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = DriverLoginSerializer

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
            "role": "driver",
        }, status=status.HTTP_200_OK)