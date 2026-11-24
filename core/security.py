"""
Utilidades de seguridad compartidas por todo el sitio.

- get_client_ip(): IP real del visitante, resistente a falsificación.
- SecurityHeadersMiddleware: redirige hosts secundarios al dominio canónico
  y agrega la cabecera Permissions-Policy.
"""
import ipaddress
import logging

from django.conf import settings
from django.http import HttpResponsePermanentRedirect

logger = logging.getLogger('leads')


def _ip_valida(valor):
    try:
        return str(ipaddress.ip_address((valor or '').strip()))
    except ValueError:
        return ''


def get_client_ip(request):
    """
    Devuelve la IP del visitante.

    El sitio está detrás de Cloudflare (Render), que SIEMPRE sobrescribe
    CF-Connecting-IP con la IP real de quien se conectó: el cliente no puede
    falsificarla. X-Forwarded-For, en cambio, acepta valores inventados por el
    cliente al inicio de la lista, por eso solo se usa como respaldo.

    Se usa para el rate limit de leads y para el bloqueo de django-axes
    (AXES_CLIENT_IP_CALLABLE).
    """
    ip = _ip_valida(request.META.get('HTTP_CF_CONNECTING_IP'))
    if ip:
        return ip

    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        ip = _ip_valida(xff.split(',')[0])
        if ip:
            logger.debug("IP de cliente obtenida desde X-Forwarded-For (sin CF-Connecting-IP)")
            return ip

    return _ip_valida(request.META.get('REMOTE_ADDR')) or '0.0.0.0'


class SecurityHeadersMiddleware:
    """
    - Redirige (301) los hosts de CANONICAL_REDIRECT_HOSTS (p. ej. el subdominio
      *.onrender.com) al dominio canónico, para que el sitio no quede publicado
      dos veces.
    - Agrega Permissions-Policy: el sitio no usa cámara, micrófono, ubicación,
      pagos ni USB, así que se desactivan para cualquier script.
    """

    PERMISSIONS_POLICY = (
        'camera=(), microphone=(), geolocation=(), payment=(), usb=(), '
        'magnetometer=(), gyroscope=(), accelerometer=()'
    )

    def __init__(self, get_response):
        self.get_response = get_response
        self.canonical = getattr(settings, 'CANONICAL_HOST', '')
        self.redirect_hosts = {h.lower() for h in getattr(settings, 'CANONICAL_REDIRECT_HOSTS', ())}

    def __call__(self, request):
        if self.canonical and self.redirect_hosts:
            host = request.get_host().split(':')[0].lower()
            if host in self.redirect_hosts:
                return HttpResponsePermanentRedirect(f'https://{self.canonical}{request.get_full_path()}')

        response = self.get_response(request)
        response.setdefault('Permissions-Policy', self.PERMISSIONS_POLICY)
        return response
