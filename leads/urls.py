from django.urls import path
from . import views

urlpatterns = [
    path('nuevo/', views.nuevo_lead, name='nuevo_lead'),
    path('calcular/', views.calcular_lead, name='calcular_lead'),
    path('diagnostico/', views.guardar_diagnostico, name='guardar_diagnostico'),
]
