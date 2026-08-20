from django.contrib import admin
from .models import Provider, AvailabilityRule, TimeSlotOverride

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
    inlines = [AvailabilityRuleInline, TimeSlotOverrideInline]

    fieldsets = (
        (None, {
            'fields': ('user', 'display_name', 'bio', 'bio_en', 'bio_de', 'profile_image')
        }),
    )