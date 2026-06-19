from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from datetime import date

PRIORITY_MAP = {
    'landing':              1.0,
    'comparar_isapres':     0.9,
    'plan_economico':       0.9,
    'isapre_o_fonasa':      0.9,
    'cuanto_cuesta_isapre': 0.85,
    'isapre_para_familia':  0.85,
    'clinica_davila':       0.85,
    'clinica_alemana':      0.85,
    'clinica_las_condes':   0.85,
    'privacidad':           0.3,
    'terminos':             0.3,
}

class StaticSitemap(Sitemap):
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return [
            'landing',
            'comparar_isapres',
            'plan_economico',
            'isapre_o_fonasa',
            'cuanto_cuesta_isapre',
            'isapre_para_familia',
            'clinica_davila',
            'clinica_alemana',
            'clinica_las_condes',
            'privacidad',
            'terminos',
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return PRIORITY_MAP.get(item, 0.5)

    def lastmod(self, item):
        return date.today()
