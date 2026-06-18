from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.views.generic import RedirectView
from core.sitemaps import StaticSitemap
from core import views as core_views

sitemaps = {'static': StaticSitemap}

urlpatterns = [
    path('gestion-interna/', admin.site.urls),
    path('', include('core.urls')),
    path('leads/', include('leads.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', core_views.robots_txt, name='robots'),
    path('favicon.ico', RedirectView.as_view(url='/static/img/favicon.svg', permanent=True)),
]
