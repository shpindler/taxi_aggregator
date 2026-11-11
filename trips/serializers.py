from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from django.contrib.auth.models import User
from .models import Trip, TripStatus
from drivers.models import Driver
from passengers.models import Passenger


class TripReadSerializer(serializers.ModelSerializer):
    """Для чтения: отдаём вложенные данные водителя и пассажира."""

    driver_email = serializers.EmailField(source="driver.user.email", read_only=True)
    driver_phone = serializers.CharField(source="driver.phone", read_only=True)
    driver_name = serializers.SerializerMethodField()

    passenger_email = serializers.EmailField(source="passenger.user.email", read_only=True)
    passenger_phone = serializers.CharField(source="passenger.phone", read_only=True)
    passenger_name = serializers.SerializerMethodField()

    pickup = GeometryField(read_only=True)
    destination = GeometryField(read_only=True)

    class Meta:
        model = Trip
        fields = [
            "id",
            "status",
            "pickup",
            "destination",
            "driver",
            "driver_email",
            "driver_phone",
            "driver_name",
            "passenger",
            "passenger_email",
            "passenger_phone",
            "passenger_name",
            "price",
            "mark",
            "created_at",
            "updated_at",
        ]

    def get_driver_name(self, obj):
        if not obj.driver:
            return None
        return f"{obj.driver.user.first_name} {obj.driver.user.last_name}".strip()

    def get_passenger_name(self, obj):
        if not obj.passenger:
            return None
        return f"{obj.passenger.user.first_name} {obj.passenger.user.last_name}".strip()


class TripWriteSerializer(serializers.ModelSerializer):
    """Для создания/обновления поездки."""
    pickup = GeometryField()
    destination = GeometryField()

    class Meta:
        model = Trip
        fields = [
            "id",
            "status",
            "pickup",
            "destination",
            "driver",
            "passenger",
            "fare",
            "status",
            "distance_km",
            "created_at",
            "mark",
        ]
        read_only_fields = ["id", "created_at"]
    
    def validate_mark(self, value):
        if value < 0 or value > 5:
            raise serializers.ValidationError(
                "Оценка может быть только больше либо равна 0"
                " и меньше либо равна 5."
            )
    
    def validate_distance_km(self, value):
        if value < 0:
            raise serializer.ValidationError(
                "Дистанция должна быть больше либо равна 0"
            )

    def validate(self, attrs):
        # Пример бизнес-правила: водитель не может быть занят другой активной поездкой
        driver = attrs.get("driver", getattr(self.instance, "driver", None))
        if driver and driver.is_available is False:
            raise serializers.ValidationError(
                {"driver": "Driver is not available"}
            )
        return attrs