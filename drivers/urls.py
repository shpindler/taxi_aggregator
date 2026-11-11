# drivers/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import DriverViewSet, DriverLoginViewSet

router = DefaultRouter()
router.register(r"", DriverViewSet, basename="driver")

urlpatterns = [
    path("auth/login/", DriverLoginViewSet.as_view({"post": "create"}), name="driver-login"),
    *router.urls,
]