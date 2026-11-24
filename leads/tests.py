from django.core.cache import caches
from django.test import TestCase as DjangoTestCase, override_settings

from .models import Lead

CACHES_TEST = {
    'default':    {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'test-default'},
    'rate_limit': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'test-rl'},
}
# Sin manifiesto de collectstatic en tests
STORAGES_TEST = {
    'default':     {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


@override_settings(STORAGES=STORAGES_TEST)
class TestCase(DjangoTestCase):
    """Limpia la caché de páginas y el rate limit entre tests."""

    def setUp(self):
        super().setUp()
        for c in caches.all():
            c.clear()

DATOS_VALIDOS = {
    'nombre': 'Persona Prueba',
    'rut': '11.111.111-1',
    'telefono': '9 1234 5678',
    'email': 'prueba@ejemplo.cl',
}


@override_settings(CACHES=CACHES_TEST)
class NuevoLeadTest(TestCase):

    def test_lead_valido_se_guarda_y_marca_evento_meta(self):
        resp = self.client.post('/leads/nuevo/', DATOS_VALIDOS)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['success'])
        lead = Lead.objects.get()
        self.assertEqual(self.client.session['meta_lead_event'], f'lead-{lead.pk}')

    def test_lead_invalido_no_marca_evento(self):
        resp = self.client.post('/leads/nuevo/', {**DATOS_VALIDOS, 'rut': '11.111.111-2'})
        self.assertEqual(resp.status_code, 400)
        self.assertNotIn('meta_lead_event', self.client.session)

    def test_utm_larga_se_trunca_sin_error(self):
        resp = self.client.post('/leads/nuevo/', {**DATOS_VALIDOS, 'utm_campaign': 'x' * 300,
                                                  'utm_source': 'meta', 'utm_medium': 'paid_social'})
        self.assertEqual(resp.status_code, 200)
        lead = Lead.objects.get()
        self.assertEqual(len(lead.utm_campaign), 100)
        self.assertEqual(lead.utm_source, 'meta')

    def test_formulario_clinica_guarda_situacion_y_clinica(self):
        resp = self.client.post('/leads/nuevo/', {**DATOS_VALIDOS, 'situacion': 'isapre-subio',
                                                  'clinica_preferente': 'alemana'})
        self.assertEqual(resp.status_code, 200)
        lead = Lead.objects.get()
        self.assertEqual(lead.situacion, 'isapre-subio')
        self.assertEqual(lead.clinica_preferente, 'alemana')

    def test_formulario_clinica_rechaza_valores_fuera_de_catalogo(self):
        self.client.post('/leads/nuevo/', {**DATOS_VALIDOS, 'situacion': '<script>',
                                           'clinica_preferente': 'otra'})
        lead = Lead.objects.get()
        self.assertEqual(lead.situacion, '')
        self.assertEqual(lead.clinica_preferente, '')


@override_settings(CACHES=CACHES_TEST)
class GraciasMetaLeadTest(TestCase):

    def test_evento_lead_se_dispara_una_sola_vez(self):
        self.client.post('/leads/nuevo/', DATOS_VALIDOS)
        lead = Lead.objects.get()

        primera = self.client.get('/gracias/')
        self.assertContains(primera, f'data-event-id="lead-{lead.pk}"')
        self.assertIn('no-store', primera['Cache-Control'])

        recarga = self.client.get('/gracias/')
        self.assertNotContains(recarga, 'id="meta-lead"')

    def test_gracias_sin_envio_no_dispara_lead(self):
        resp = self.client.get('/gracias/')
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'id="meta-lead"')


@override_settings(CACHES=CACHES_TEST)
class MetaPixelTest(TestCase):

    @override_settings(DEBUG=False, META_PIXEL_ID='3609526355889947')
    def test_pixel_presente_en_produccion(self):
        resp = self.client.get('/privacidad/')
        self.assertContains(resp, 'id="meta-pixel-cfg" data-id="3609526355889947"', count=1)
        self.assertContains(resp, 'js/meta-pixel')

    @override_settings(DEBUG=False, META_PIXEL_ID='')
    def test_pixel_desactivable_por_variable(self):
        resp = self.client.get('/privacidad/')
        self.assertNotContains(resp, 'meta-pixel')

    @override_settings(DEBUG=True, META_PIXEL_ID='3609526355889947')
    def test_pixel_ausente_en_desarrollo(self):
        resp = self.client.get('/privacidad/')
        self.assertNotContains(resp, 'meta-pixel')

    def test_csp_permite_meta(self):
        resp = self.client.get('/privacidad/')
        csp = resp['Content-Security-Policy']
        self.assertIn('https://connect.facebook.net', csp)
        self.assertNotIn("'unsafe-inline'", csp.split('script-src')[1].split(';')[0])

    @override_settings(DEBUG=False, META_PIXEL_ID='3609526355889947')
    def test_landing_clinica_sin_script_inline_y_form_post(self):
        resp = self.client.get('/isapre-clinica-alemana/')
        html = resp.content.decode()
        self.assertIn('method="post" action="/leads/nuevo/"', html)
        self.assertIn('name="rut"', html)
        self.assertIn('js/form-clinica', html)
        self.assertNotIn('onfocus=', html)
        # Solo scripts con src o JSON-LD (no ejecutables): nada que la CSP bloquee
        import re
        for tag in re.findall(r'<script(?![^>]*\bsrc=)([^>]*)>', html):
            self.assertIn('application/ld+json', tag)
