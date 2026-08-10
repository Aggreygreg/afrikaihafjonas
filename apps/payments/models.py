"""
apps.payments — DECOMMISSIONED

This module was intentionally disabled when the platform pivoted from
third-party payment gateways (Stripe, PayPal) to manual bank transfers.
All payment logic now lives on the AppointmentRequest model in apps.bookings.

This file is kept (empty) to prevent import errors. The app is removed
from INSTALLED_APPS and its migrations are deleted.
"""
