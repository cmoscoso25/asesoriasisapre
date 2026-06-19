from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('gracias/', views.gracias, name='gracias'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('terminos/', views.terminos, name='terminos'),

    # Landing pages por clínica
    path('isapre-clinica-davila/',     views.isapre_clinica, {'slug': 'davila'},     name='clinica_davila'),
    path('isapre-clinica-alemana/',    views.isapre_clinica, {'slug': 'alemana'},    name='clinica_alemana'),
    path('isapre-clinica-las-condes/', views.isapre_clinica, {'slug': 'las-condes'}, name='clinica_las_condes'),

    # Landing pages informativas
    path('comparar-isapres-chile/',          views.comparar_isapres,    name='comparar_isapres'),
    path('plan-isapre-economico/',           views.plan_economico,      name='plan_economico'),
    path('isapre-o-fonasa/',                 views.isapre_o_fonasa,     name='isapre_o_fonasa'),
    path('cuanto-cuesta-isapre-chile/',      views.cuanto_cuesta_isapre,name='cuanto_cuesta_isapre'),
    path('isapre-para-familia/',             views.isapre_para_familia, name='isapre_para_familia'),

    # Redirects 301 — URLs antiguas con .html → nuevas URLs limpias
    path('isapre-clinica-davila.html',           RedirectView.as_view(url='/isapre-clinica-davila/',     permanent=True)),
    path('isapre-clinica-alemana.html',          RedirectView.as_view(url='/isapre-clinica-alemana/',    permanent=True)),
    path('isapre-clinica-las-condes.html',       RedirectView.as_view(url='/isapre-clinica-las-condes/',permanent=True)),
    path('comparar-isapres-chile.html',          RedirectView.as_view(url='/comparar-isapres-chile/',    permanent=True)),
    path('plan-isapre-economico.html',           RedirectView.as_view(url='/plan-isapre-economico/',     permanent=True)),
    path('isapre-o-fonasa.html',                 RedirectView.as_view(url='/isapre-o-fonasa/',           permanent=True)),
    path('cuanto-cuesta-isapre-chile.html',      RedirectView.as_view(url='/cuanto-cuesta-isapre-chile/',permanent=True)),
    path('isapre-para-familia.html',             RedirectView.as_view(url='/isapre-para-familia/',       permanent=True)),
    path('mejor-isapre-chile.html',              RedirectView.as_view(url='/comparar-isapres-chile/',    permanent=True)),
    path('isapres-mas-baratas-chile.html',       RedirectView.as_view(url='/plan-isapre-economico/',     permanent=True)),
    path('fonasa-a-isapre.html',                 RedirectView.as_view(url='/isapre-o-fonasa/',           permanent=True)),
    path('isapre-sin-preexistencias-chile.html', RedirectView.as_view(url='/',                           permanent=True)),
]
