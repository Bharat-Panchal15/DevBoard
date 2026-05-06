from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username

class OTPCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="otp_code")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)
    
    def __str__(self):
        return f"OTP for {self.user.username}"