import logging
import traceback

from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.cache import cache
from .forms import LeadForm
from .notifications import notificar_asesor

logger = logging.getLogger(__name__)


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
        intentos = cache.get(cache_key, 0)

        if intentos >= 3:
            return JsonResponse({
                'success': False,
                'error': 'Demasiados intentos. Intenta en unos minutos o escríbenos por WhatsApp.'
            }, status=429)

        form = LeadForm(request.POST)

        if form.is_valid():
            lead = form.save(commit=False)
            lead.ip_address = ip
            lead.utm_source = request.GET.get('utm_source', request.POST.get('utm_source', ''))
            lead.utm_medium = request.GET.get('utm_medium', request.POST.get('utm_medium', ''))
            lead.utm_campaign = request.GET.get('utm_campaign', request.POST.get('utm_campaign', ''))

            diag = request.session.get('diagnostico', {})
            # or '' convierte None (JSON null) a '' para todos los CharField
            lead.situacion        = diag.get('situacion')        or ''
            lead.renta            = diag.get('renta')
            lead.cargas           = diag.get('cargas')           or ''
            lead.clinica_preferente = diag.get('clinica')        or ''
            lead.prevision_actual = diag.get('prevision_actual') or ''
            lead.pago_actual      = diag.get('pago_actual')
            lead.preferencia      = diag.get('preferencia')      or ''
            lead.ahorro_estimado_min = diag.get('ahorro_min')
            lead.ahorro_estimado_max = diag.get('ahorro_max')
            lead.isapres_recomendadas = diag.get('isapres') or []

            try:
                edad_val = int(request.POST.get('edad-input', 0))
                lead.edad = edad_val if 18 <= edad_val <= 100 else None
            except (ValueError, TypeError):
                lead.edad = None

            lead.save()
            cache.set(cache_key, intentos + 1, 600)

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
def guardar_diagnostico(request):
    import json
    try:
        data = json.loads(request.body)
        request.session['diagnostico'] = {
            'situacion':        data.get('situacion')        or '',
            'prevision_actual': data.get('prevision_actual') or '',
            'pago_actual':      data.get('pago_actual'),
            'renta':            data.get('renta'),
            'cargas':           data.get('cargas')           or '',
            'clinica':          data.get('clinica')          or '',
            'preferencia':      data.get('preferencia')      or '',
            'ahorro_min':       data.get('ahorro_min'),
            'ahorro_max':       data.get('ahorro_max'),
            'isapres':          data.get('isapres')          or [],
        }
        return JsonResponse({'success': True})
    except Exception:
        logger.error("Error en guardar_diagnostico:\n%s", traceback.format_exc())
        return JsonResponse({'success': False}, status=400)
