from django.contrib.gis.db import models as gis_models
from django.db import models

# Create your models here.

class TripStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Trip(models.Model):
    passenger = models.ForeignKey(
        "passengers.Passenger",
        on_delete=models.PROTECT,
        related_name="trips",
    )
    driver = models.ForeignKey(
        "drivers.Driver",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="trips",
    )

    pickup = gis_models.PointField(srid=4326, geography=True)
    destination = gis_models.PointField(srid=4326, geography=True)

    status = models.CharField(
        max_length=20, choices=TripStatus.choices, default=TripStatus.PENDING
    )
    fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    mark = models.IntegerField(default=5)

    class Meta:
        db_table = "trips"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["passenger", "status"]),
            gis_models.Index(fields=["pickup"]),
            gis_models.Index(fields=["destination"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=TripStatus.values),
                name="trip_status_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"Trip #{self.pk} [{self.status}]"