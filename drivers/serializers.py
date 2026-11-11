# drivers/serializers.py
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework_gis.serializers import GeoModelSerializer

from taxi_aggregator.utils.phone import normalize_phone
from .models import Driver, CarClass
from trips.models import Trip

User = get_user_model()


class DriverReadSerializer(GeoModelSerializer):
    """Для отдачи данных водителя (GET)."""
    user_id = serializers.CharField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = [
            "id",
            "user_id",
            "email",
            "first_name",
            "last_name",
            "location",
            "is_available",
            "car_class",
            "rating",
        ]
        read_only_fields = ["id", "rating"]
        geo_field = "location"

    def get_rating(self, obj: Driver) -> float:
        trips = Trip.objects.filter(driver_id=obj.id)
        if trips.count():
            rating = 0
            for trip in trips:
                rating += trip.mark
            return rating / trips.count()
        else:
            return 0


class DriverWriteSerializer(GeoModelSerializer):
    """Для создания/обновления профиля водителя."""

    # Поля пользователя, которые нужно принимать на вход
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Driver
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
            "is_available",
            "car_class",
            "phone",
            "drivers_license",
            "vehicle_registration_certificate",
            "taxi_register_extract",
        ]
    
    def validate_email(self, value):
        _value = value.lower()
        if User.objects.filter(email=_value).exists():
            raise serializers.ValidationError("User with this email already exists")
        return _value

    def validate_phone(self, value):
        _value = normalize_phone(value)
        if Driver.objects.filter(phone=_value).exists():
            raise serializers.ValidationError("Driver with this phone already exists")
        return _value

    def validate_car_class(self, value: str) -> str:
        allowed = {choice[0] for choice in CarClass.choices}
        if value not in allowed:
            raise serializers.ValidationError(
                f"car_class must be one of {sorted(allowed)}"
            )
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        # Вытаскиваем данные пользователя из validated_data
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        first_name = validated_data.pop("first_name", "")
        last_name = validated_data.pop("last_name", "")

        # Создаём пользователя
        user = User.objects.create_user(
            username=validated_data["phone"],
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Создаём профиль водителя
        driver = Driver.objects.create(user=user, **validated_data)
        return driver


class DriverLocationSerializer(GeoModelSerializer):
    """Только геолокация и статус доступности — для частых обновлений."""

    class Meta:
        model = Driver
        fields = ["location", "is_available"]
        geo_field = "location"


# taxi_aggregator/auth_common.py
from rest_framework import serializers
from django.contrib.auth.models import User


class BaseLoginSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login = attrs["login"].strip()
        password = attrs["password"]

        driver = (
            Driver.objects.filter(phone__iexact=login).first()
        )

        if not driver or not driver.user.check_password(password):
            raise serializers.ValidationError({"detail": "Invalid credentials"})

        if not driver.user.is_active:
            raise serializers.ValidationError({"detail": "User is inactive"})

        attrs["user"] = driver.user
        return attrs


class DriverLoginSerializer(BaseLoginSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = attrs["user"]

        if not hasattr(user, "driver"):
            raise serializers.ValidationError(
                {"detail": "This account is not a driver"}
            )

        driver = user.driver
        if driver.verification_status != "approved":
            raise serializers.ValidationError(
                {"detail": f"Driver verification status: {driver.verification_status}"}
            )

        attrs["driver"] = driver
        return attrs