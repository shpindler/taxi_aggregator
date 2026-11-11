# passengers/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PassengerViewSet, PassengerLoginViewSet

router = DefaultRouter()
router.register(r"", PassengerViewSet, basename="passenger")

urlpatterns = [
    path("auth/login/", PassengerLoginViewSet.as_view({"post": "create"}), name="passenger-login"),
    *router.urls,
]