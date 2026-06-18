from django.shortcuts import render
from django.http import HttpResponse

def landing(request):
    return render(request, 'core/landing.html')

def gracias(request):
    lead_nombre = request.session.get('lead_nombre', '')
    return render(request, 'core/gracias.html', {'lead_nombre': lead_nombre})

def privacidad(request):
    return render(request, 'core/privacidad.html')

def terminos(request):
    return render(request, 'core/terminos.html')

def robots_txt(request):
    content = """User-agent: *
Allow: /
Disallow: /gestion-interna/
Disallow: /leads/
Sitemap: https://asesoriasisapres.com/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')
