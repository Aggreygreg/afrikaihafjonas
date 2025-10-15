from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Custom user model to extend the default Django user.
    """
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CLIENT = "CLIENT", "Client"

    class ContactPreference(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        WHATSAPP = "WHATSAPP", "WhatsApp"

    role = models.CharField(
        max_length=50, choices=Role.choices, default=Role.CLIENT
    )
    contact_preference = models.CharField(
        max_length=50, choices=ContactPreference.choices, default=ContactPreference.EMAIL
    )