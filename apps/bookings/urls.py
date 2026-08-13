from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('book/<int:service_pk>/', views.consult_wizard_view, name='book_service'),
    path('book/<int:service_pk>/step3/', views.wizard_step_3, name='wizard_step_3'),
    path('book/<int:service_pk>/step4/', views.wizard_step_4, name='wizard_step_4'),
    path('confirmation/<str:reference>/', views.confirmation, name='confirmation'),
    path('ajax/load-slots/', views.load_available_slots_view, name='load_slots'),
    path('status/', views.guest_lookup_view, name='booking_status'),
    path('ajax/payment-detail/', views.payment_detail_fields, name='payment_detail'),
]
