from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'gateway', 'status', 'created_at')
    list_filter = ('gateway', 'status')
    search_fields = ('gateway_transaction_id', 'booking__booking_code')
    readonly_fields = ('booking', 'amount', 'gateway', 'gateway_transaction_id', 'status', 'created_at')

    # Payments should not be manually created, changed, or deleted from the admin.
    # They are records of transactions handled by the payment gateway.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False