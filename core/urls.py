from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('gracias/', views.gracias, name='gracias'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('terminos/', views.terminos, name='terminos'),

    # Landing pages por clínica
    path('isapre-clinica-davila/', views.isapre_clinica, {'slug': 'davila'}, name='clinica_davila'),
    path('isapre-clinica-alemana/', views.isapre_clinica, {'slug': 'alemana'}, name='clinica_alemana'),
    path('isapre-clinica-las-condes/', views.isapre_clinica, {'slug': 'las-condes'}, name='clinica_las_condes'),

    # Landing pages informativas
    path('comparar-isapres-chile/', views.comparar_isapres, name='comparar_isapres'),
    path('plan-isapre-economico/', views.plan_economico, name='plan_economico'),

    # Redirects 301 desde URLs antiguas con .html
    path('isapre-clinica-davila.html',    RedirectView.as_view(url='/isapre-clinica-davila/',    permanent=True)),
    path('isapre-clinica-alemana.html',   RedirectView.as_view(url='/isapre-clinica-alemana/',   permanent=True)),
    path('isapre-clinica-las-condes.html',RedirectView.as_view(url='/isapre-clinica-las-condes/',permanent=True)),
    path('comparar-isapres-chile.html',   RedirectView.as_view(url='/comparar-isapres-chile/',   permanent=True)),
    path('plan-isapre-economico.html',    RedirectView.as_view(url='/plan-isapre-economico/',    permanent=True)),
]
