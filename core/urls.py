from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('gracias/', views.gracias, name='gracias'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('terminos/', views.terminos, name='terminos'),
]
