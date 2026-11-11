from django.contrib import admin
from .models import Driver


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "phone", "car_class", "is_available")
    list_filter = ("car_class", "is_available")
    search_fields = ("user__email", "phone", "user__first_name", "user__last_name")
    # readonly_fields = ("created_at", "updated_at")  # если такие поля есть