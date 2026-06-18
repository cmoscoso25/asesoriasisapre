from django.conf import settings as django_settings

def seo_defaults(request):
    return {
        'meta_title': 'Cotizar Isapre Gratis Chile 2026 | AsesoríasIsapres.com',
        'meta_description': 'Asesoría gratuita para cotizar y comparar isapres en Chile. Diagnóstico en 60 segundos según tu sueldo, edad y clínica. ¿Tu isapre subió el precio? Puedes cambiarte ahora sin penalización.',
        'og_image': 'https://asesoriasisapres.com/static/img/og-image.jpg',
        'canonical_url': f"https://asesoriasisapres.com{request.path}",
        'whatsapp_number': '56964345927',
        'tawkto_id': getattr(django_settings, 'TAWKTO_ID', ''),
    }
