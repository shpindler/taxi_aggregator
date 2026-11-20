# models.py (примерная структура)
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random


class PhoneVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='phone_verification')
    phone_number = models.CharField(max_length=20, blank=True)
    otp_code = models.CharField(max_length=6, blank=True)
    created_at = models.DateTimeField(auto_now=True)
    attempts = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)

    def generate_otp(self):
        self.otp_code = str(random.randint(100000, 999999))
        self.created_at = timezone.now()
        self.attempts = 0
        self.save()
        return self.otp_code

    def is_valid(self):
        # Код живет, например, 5 минут
        return (timezone.now() - self.created_at).total_seconds() < 300