from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import SiteConfiguration

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(SingletonModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('hero_title', 'hero_subtitle', 'hero_image'),
        }),
    )

