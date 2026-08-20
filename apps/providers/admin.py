from django.contrib import admin
from .models import Provider, ProviderTranslation, AvailabilityRule, TimeSlotOverride

class ProviderTranslationInline(admin.StackedInline):
    model = ProviderTranslation
    extra = 3  # HU, EN, DE by default

class AvailabilityRuleInline(admin.TabularInline):
    model = AvailabilityRule
    extra = 1 # Show one extra blank form by default

class TimeSlotOverrideInline(admin.TabularInline):
    model = TimeSlotOverride
    extra = 1

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'user')
    search_fields = ('display_name', 'user__username')
    inlines = [ProviderTranslationInline, AvailabilityRuleInline, TimeSlotOverrideInline]

    fieldsets = (
        (None, {
            'fields': ('user', 'display_name', 'profile_image')
        }),
    )