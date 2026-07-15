from django.contrib import admin
from .models import Service, ParentCategory, ServiceCategory, ServiceImage, ServiceOption

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1 
    ordering = ('order',)

class ServiceOptionInline(admin.TabularInline):
    model = ServiceOption
    extra = 1 

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'base_price', 'duration_minutes', 'is_popular')
    list_filter = ('category__parent', 'category', 'is_popular', 'providers') # Added parent filter
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

@admin.register(ParentCategory)
class ParentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent') # Show parent in the list
    list_filter = ('parent',) # Allow filtering by parent
    search_fields = ('name',)
    ordering = ('parent', 'name')