
from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models

# Create your models here.
class Passenger(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="passenger",
    )
    location = gis_models.PointField(srid=4326, geography=True, null=True)
    phone = models.CharField(max_length=16)
