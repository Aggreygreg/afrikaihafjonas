from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating')
    list_editable = ('is_approved',)
    search_fields = ('booking__booking_code', 'comment')
    readonly_fields = ('booking', 'rating', 'comment', 'created_at')

    # Disables the ability to add reviews from the admin, as they should only
    # be created by clients after a completed booking.
    def has_add_permission(self, request):
        return False