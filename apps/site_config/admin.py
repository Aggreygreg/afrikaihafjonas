from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import SiteConfiguration

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(SingletonModelAdmin):
    fieldsets = (
        ('Hero Section', {
            'fields': ('hero_title', 'hero_subtitle', 'hero_image'),
        }),
        ('Footer Contact Info', {
            'fields': ('salon_address', 'salon_phone', 'salon_email'),
        }),
        ('Footer Social Media', {
            'fields': ('social_instagram', 'social_facebook', 'social_tiktok'),
        }),
    )