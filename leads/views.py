import json
import logging
import traceback

from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.cache import caches, cache

from .forms import LeadForm
from .notifications import notificar_asesor
from .diagnostico import (
    calcular,
    VALID_SITUACION, VALID_CARGAS, VALID_CLINICA,
    VALID_PREFERENCIA, VALID_REGION, VALID_PREVISION,
)

logger = logging.getLogger(__name__)


def _rate_cache():
    try:
        return caches['rate_limit']
    except Exception:
        return cache


def _val_choice(val, valid_set, default=''):
    s = str(val or '').strip()[:30]
    return s if s in valid_set else default


def _val_int(val, min_val=0, max_val=10_000_000):
    if val is None:
        return None
    try:
        n = int(val)
        return n if min_val <= n <= max_val else None
    except (TypeError, ValueError):
        return None


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


@csrf_protect
@require_POST
def nuevo_lead(request):
    try:
        ip = get_client_ip(request)
        cache_key = f'lead_limit_{ip}'
        rl = _rate_cache()
        intentos = rl.get(cache_key, 0)

        if intentos >= 3:
            return JsonResponse({
                'success': False,
                'error': 'Demasiados intentos. Intenta en unos minutos o escríbenos por WhatsApp.'
            }, status=429)

        form = LeadForm(request.POST)

        if form.is_valid():
            lead = form.save(commit=False)
            lead.ip_address = ip
            lead.utm_source   = request.GET.get('utm_source',   request.POST.get('utm_source', ''))
            lead.utm_medium   = request.GET.get('utm_medium',   request.POST.get('utm_medium', ''))
            lead.utm_campaign = request.GET.get('utm_campaign', request.POST.get('utm_campaign', ''))

            diag = request.session.get('diagnostico', {})
            lead.situacion          = _val_choice(diag.get('situacion'),        VALID_SITUACION)
            lead.renta              = _val_int(diag.get('renta'),        0, 10_000_000)
            lead.cargas             = _val_choice(diag.get('cargas'),           VALID_CARGAS)
            lead.clinica_preferente = _val_choice(diag.get('clinica'),          VALID_CLINICA)
            lead.prevision_actual   = _val_choice(diag.get('prevision_actual'), VALID_PREVISION)
            lead.pago_actual        = _val_int(diag.get('pago_actual'),  0, 5_000_000)
            lead.preferencia        = _val_choice(diag.get('preferencia'),      VALID_PREFERENCIA)
            if not lead.region:
                lead.region         = _val_choice(diag.get('region'),           VALID_REGION)
            lead.ahorro_estimado_min  = _val_int(diag.get('ahorro_min'), 0, 5_000_000)
            lead.ahorro_estimado_max  = _val_int(diag.get('ahorro_max'), 0, 5_000_000)
            lead.isapres_recomendadas = [
                str(x)[:30] for x in (diag.get('isapres') or []) if isinstance(x, str)
            ][:5]

            try:
                edad_val = int(request.POST.get('edad-input', 0))
                lead.edad = edad_val if 18 <= edad_val <= 100 else None
            except (ValueError, TypeError):
                lead.edad = None

            lead.save()
            rl.set(cache_key, intentos + 1, 600)

            request.session['lead_nombre'] = lead.nombre
            notificar_asesor(lead)

            return JsonResponse({'success': True, 'redirect': '/gracias/'})

        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    except Exception:
        logger.error("Error en nuevo_lead:\n%s", traceback.format_exc())
        return JsonResponse(
            {'success': False, 'error': 'Error interno. Por favor intenta de nuevo.'},
            status=500
        )


@csrf_protect
@require_POST
def calcular_lead(request):
    """Calcula diagnóstico en servidor y guarda resultado en sesión."""
    try:
        data = json.loads(request.body)

        situacion   = _val_choice(data.get('situacion'),        VALID_SITUACION,   '')
        cargas      = _val_choice(data.get('cargas'),           VALID_CARGAS,      'solo')
        clinica     = _val_choice(data.get('clinica'),          VALID_CLINICA,     'sin-preferencia')
        preferencia = _val_choice(data.get('preferencia'),      VALID_PREFERENCIA, '')
        region      = _val_choice(data.get('region'),           VALID_REGION,      '')
        prevision   = _val_choice(data.get('prevision_actual'), VALID_PREVISION,   '')
        renta       = _val_int(data.get('renta'),       0, 10_000_000)
        pago_actual = _val_int(data.get('pago_actual'), 0,  5_000_000)

        resultado = calcular(renta or 0, cargas, situacion, clinica, pago_actual)

        request.session['diagnostico'] = {
            'situacion':        situacion,
            'prevision_actual': prevision,
            'pago_actual':      pago_actual,
            'renta':            renta,
            'cargas':           cargas,
            'clinica':          clinica,
            'preferencia':      preferencia,
            'region':           region,
            'ahorro_min':       resultado['ahorroMin'],
            'ahorro_max':       resultado['ahorroMax'],
            'isapres':          [p['isapre'] for p in resultado['planes'][:3]],
        }

        return JsonResponse({'success': True, 'resultado': resultado})

    except Exception:
        logger.error("Error en calcular_lead:\n%s", traceback.format_exc())
        return JsonResponse({'success': False}, status=400)


@csrf_protect
@require_POST
def guardar_diagnostico(request):
    """Endpoint legado — mantener para JS en caché de versiones anteriores."""
    try:
        data = json.loads(request.body)
        request.session['diagnostico'] = {
            'situacion':        _val_choice(data.get('situacion'),        VALID_SITUACION),
            'prevision_actual': _val_choice(data.get('prevision_actual'), VALID_PREVISION),
            'pago_actual':      _val_int(data.get('pago_actual'),  0, 5_000_000),
            'renta':            _val_int(data.get('renta'),        0, 10_000_000),
            'cargas':           _val_choice(data.get('cargas'),           VALID_CARGAS),
            'clinica':          _val_choice(data.get('clinica'),          VALID_CLINICA),
            'preferencia':      _val_choice(data.get('preferencia'),      VALID_PREFERENCIA),
            'region':           _val_choice(data.get('region'),           VALID_REGION),
            'ahorro_min':       _val_int(data.get('ahorro_min'),   0, 5_000_000),
            'ahorro_max':       _val_int(data.get('ahorro_max'),   0, 5_000_000),
            'isapres':          [
                str(x)[:30] for x in (data.get('isapres') or []) if isinstance(x, str)
            ][:5],
        }
        return JsonResponse({'success': True})
    except Exception:
        logger.error("Error en guardar_diagnostico:\n%s", traceback.format_exc())
        return JsonResponse({'success': False}, status=400)
