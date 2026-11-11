from django.contrib import admin
from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("id", "passenger", "driver", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("passenger__user__email", "driver__user__email")
    date_hierarchy = "created_at"
