from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from leads.diagnostico import PLANES_DB, UF

CLINICAS = {
    'davila': {
        'slug':        'davila',
        'nombre':      'Clínica Dávila',
        'titulo':      'Isapre para Clínica Dávila: planes, cobertura y asesoría 2026',
        'descripcion': 'Compara los mejores planes de isapre con cobertura en Clínica Dávila. Precios desde 1,05 UF/mes. Asesoría gratuita y personalizada.',
        'intro':       'Clínica Dávila es una de las redes de salud privada más elegidas de Chile por su cobertura nacional y calidad de atención. Si quieres asegurarte de poder atenderte en Dávila sin pagar de más, aquí comparamos los planes de isapre disponibles para ti.',
        'key':         'davila',
    },
    'alemana': {
        'slug':        'alemana',
        'nombre':      'Clínica Alemana',
        'titulo':      'Isapre para Clínica Alemana: planes, cobertura y asesoría 2026',
        'descripcion': 'Compara planes de isapre con cobertura en Clínica Alemana. Desde Cruz Blanca hasta Banmédica. Asesoría gratuita, diagnóstico en 60 segundos.',
        'intro':       'Clínica Alemana es reconocida como una de las mejores clínicas de Latinoamérica. Tener cobertura preferente en ella requiere elegir el plan correcto. Te mostramos las opciones disponibles según tu presupuesto.',
        'key':         'alemana',
    },
    'las-condes': {
        'slug':        'las-condes',
        'nombre':      'Clínica Las Condes',
        'titulo':      'Isapre para Clínica Las Condes: planes y cobertura 2026',
        'descripcion': 'Planes de isapre con cobertura en Clínica Las Condes. Compara precios desde Cruz Blanca, Colmena y Banmédica. Asesoría 100% gratuita.',
        'intro':       'Clínica Las Condes es una de las instituciones de salud privada de mayor prestigio en Chile. Para atenderte con cobertura preferente, necesitas un plan específico. Aquí comparamos todas las opciones disponibles.',
        'key':         'las-condes',
    },
}


def _planes_con_clp(key):
    planes = PLANES_DB.get(key, [])
    return [
        {**p, 'clp': round(p['precio_uf'] * UF / 1000) * 1000}
        for p in planes
    ]


@ensure_csrf_cookie
def landing(request):
    return render(request, 'core/landing.html')


def gracias(request):
    lead_nombre = request.session.get('lead_nombre', '')
    return render(request, 'core/gracias.html', {'lead_nombre': lead_nombre})


def privacidad(request):
    return render(request, 'core/privacidad.html')


def terminos(request):
    return render(request, 'core/terminos.html')


@ensure_csrf_cookie
def isapre_clinica(request, slug):
    clinica = CLINICAS.get(slug)
    if not clinica:
        from django.http import Http404
        raise Http404
    ctx = {
        'clinica': clinica,
        'planes':  _planes_con_clp(clinica['key']),
    }
    return render(request, 'core/clinica_landing.html', ctx)


@ensure_csrf_cookie
def comparar_isapres(request):
    return render(request, 'core/comparar.html', {
        'planes': _planes_con_clp('sin-preferencia'),
    })


@ensure_csrf_cookie
def plan_economico(request):
    planes = _planes_con_clp('sin-preferencia')
    return render(request, 'core/plan_economico.html', {
        'planes': planes[:4],
    })


def robots_txt(request):
    content = """User-agent: *
Allow: /
Disallow: /gestion-interna/
Disallow: /leads/
Sitemap: https://asesoriasisapres.com/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')
