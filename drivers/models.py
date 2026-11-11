from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models


class CarClass(models.TextChoices):
    ECONOMY = "economy", "Economy"
    COMFORT = "comfort", "Comfort"
    BUSINESS = "business", "Business"


class VerificationStatus(models.TextChoices):
    PENDING = "pending", "На проверке"
    APPROVED = "approved", "Одобрен"
    REJECTED = "rejected", "Отклонён"


# Create your models here.
class Driver(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="driver",
    )
    location = gis_models.PointField(srid=4326, geography=True, null=True)
    is_available = models.BooleanField(default=True)
    car_class = models.CharField(max_length=20, choices=CarClass.choices)
    phone = models.CharField(max_length=16)
    drivers_license = models.FileField(upload_to="drivers/licenses/")
    vehicle_registration_certificate = models.FileField(upload_to="drivers/vehicles/")
    taxi_register_extract = models.FileField(upload_to="drivers/taxi/")
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
        verbose_name="Статус верификации",
    )