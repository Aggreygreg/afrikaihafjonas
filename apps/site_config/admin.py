from django.contrib import admin
from solo.admin import SingletonModelAdmin

from .models import SiteConfiguration


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(SingletonModelAdmin):
    fieldsets = (
        ('Branding', {
            'fields': ('business_name', 'logo', 'favicon'),
        }),
        ('Hero Section', {
            'fields': ('hero_title', 'hero_subtitle', 'hero_image'),
        }),
        ('Contact Info', {
            'fields': ('salon_address', 'address_description', 'salon_phone', 'salon_email'),
        }),
        ('Business Hours', {
            'fields': ('business_hours',),
        }),
        ('Location & Web', {
            'fields': ('google_maps_link', 'website_url'),
        }),
        ('Social Media', {
            'fields': ('social_instagram', 'social_facebook', 'social_tiktok'),
        }),
    )
