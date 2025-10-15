from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ["username", "email", "role", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (
        ("Custom Info", {"fields": ("role", "contact_preference")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Custom Info", {"fields": ("role", "contact_preference")}),
    )

admin.site.register(CustomUser, CustomUserAdmin)