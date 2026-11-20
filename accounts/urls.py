from django.urls import path
from . import views

urlpatterns = [
    path('api/send-code/', views.send_sms_code),
    path('api/verify-code/', views.verify_sms_code),
]