from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from datetime import date

PRIORITY_MAP = {
    'landing':    1.0,
    'privacidad': 0.5,
    'terminos':   0.5,
    'gracias':    0.3,
}

class StaticSitemap(Sitemap):
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return ['landing', 'gracias', 'privacidad', 'terminos']

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return PRIORITY_MAP.get(item, 0.5)

    def lastmod(self, item):
        return date.today()
