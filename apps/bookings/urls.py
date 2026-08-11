from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('book/<int:service_pk>/', views.book_service_view, name='book_service'),
    path('ajax/load-slots/', views.load_available_slots_view, name='load_slots'),
    path('status/', views.booking_status_placeholder_view, name='booking_status'),
]