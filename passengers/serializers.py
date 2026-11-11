# drivers/serializers.py
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework_gis.serializers import GeoModelSerializer 

from taxi_aggregator.utils.phone import normalize_phone
from .models import Passenger

User = get_user_model()


class PassengerReadSerializer(GeoModelSerializer):
    """Для отдачи данных пассажира (GET)."""
    user_id = serializers.CharField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = Passenger
        fields = [
            "id",
            "user_id",
            "email",
            "location",
            "phone",
            "first_name",
            "last_name",
        ]
        read_only_fields = ["id"]
        geo_field = "location"


class PassengerWriteSerializer(GeoModelSerializer):
    """Для создания/обновления пользователя и профиля пассажира."""

    # Поля пользователя, которые нужно принимать на вход
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Passenger
        fields = [
            "phone",
            "email",
            "password",
            "first_name",
            "last_name",
        ]

    def validate_email(self, value):
        _value = value.lower()
        if User.objects.filter(email=_value).exists():
            raise serializers.ValidationError("User with this email already exists")
        return _value

    def validate_phone(self, value):
        _value = normalize_phone(value)
        if Passenger.objects.filter(phone=_value).exists():
            raise serializers.ValidationError("Passenger with this phone already exists")
        return _value

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

        # Создаём профиль пассажира
        passenger = Passenger.objects.create(user=user, **validated_data)
        return passenger

    def update(self, instance, validated_data):
        # Обновление только профиля пассажира (юзер обновляется отдельно)
        return super().update(instance, validated_data)


class PassengerLocationSerializer(GeoModelSerializer):
    """Только геолокация — для частых обновлений."""

    class Meta:
        model = Passenger
        fields = ["location"]
        geo_field = "location"


class BaseLoginSerializer(serializers.Serializer):
    login = serializers.CharField()        # email или username (= phone)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login = attrs["login"].strip()
        password = attrs["password"]

        passenger = (
            Passenger.objects.filter(phone__iexact=login).first()
        )

        if not passenger or not passenger.user.check_password(password):
            raise serializers.ValidationError({"detail": "Invalid credentials"})

        if not passenger.user.is_active:
            raise serializers.ValidationError({"detail": "User is inactive"})

        attrs["user"] = passenger.user
        return attrs


class PassengerLoginSerializer(BaseLoginSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = attrs["user"]

        if not hasattr(user, "passenger"):
            raise serializers.ValidationError(
                {"detail": "This account is not a passenger"}
            )

        attrs["passenger"] = user.passenger
        return attrs
