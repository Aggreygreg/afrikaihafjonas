from django.urls import path
from . import views

app_name = 'services'  # Namespace for our app

urlpatterns = [
    path('', views.service_list_view, name='service_list'),
    path('<int:pk>/', views.service_detail_view, name='service_detail'),
]