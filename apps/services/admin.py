from django.contrib import admin
from .models import Service, ServiceCategory, ServiceImage, ServiceOption

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1 # Show one extra blank form for images
    ordering = ('order',)

class ServiceOptionInline(admin.TabularInline):
    model = ServiceOption
    extra = 1 # Show one extra blank form for options

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'base_price', 'duration_minutes', 'is_popular')
    list_filter = ('category', 'is_popular', 'providers')
    search_fields = ('title', 'description')
    filter_horizontal = ('providers',)
    inlines = [ServiceImageInline, ServiceOptionInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'category', 'is_popular')
        }),
        ('Pricing & Duration', {
            'fields': ('base_price', 'duration_minutes')
        }),
        ('Providers', {
            'fields': ('providers',)
        }),
        ('Payment Options', {
            'fields': ('allow_full_payment', 'allow_deposit_payment', 'allow_pay_later')
        }),
        ('Optional Video', {
            'fields': ('video_url',)
        }),
    )

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)