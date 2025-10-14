from django.contrib import admin
from .models import Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'base_price', 'duration_minutes')
    search_fields = ('title', 'description')
    filter_horizontal = ('providers',) # Makes selecting providers much easier