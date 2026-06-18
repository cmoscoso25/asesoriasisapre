from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.cache import cache
from .forms import LeadForm
from .notifications import notificar_asesor


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


@csrf_protect
@require_POST
def nuevo_lead(request):
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
        lead.situacion = diag.get('situacion', '')
        lead.renta = diag.get('renta')
        lead.cargas = diag.get('cargas', '')
        lead.clinica_preferente = diag.get('clinica', '')
        lead.prevision_actual = diag.get('prevision_actual', '')
        lead.pago_actual = diag.get('pago_actual')
        lead.preferencia = diag.get('preferencia', '')
        lead.ahorro_estimado_min = diag.get('ahorro_min')
        lead.ahorro_estimado_max = diag.get('ahorro_max')
        lead.isapres_recomendadas = diag.get('isapres', [])

        try:
            edad_val = int(request.POST.get('edad-input', 0))
            lead.edad = edad_val if 18 <= edad_val <= 100 else None
        except (ValueError, TypeError):
            pass

        lead.save()
        cache.set(cache_key, intentos + 1, 600)

        request.session['lead_nombre'] = lead.nombre
        notificar_asesor(lead)

        return JsonResponse({'success': True, 'redirect': '/gracias/'})

    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@csrf_protect
@require_POST
def guardar_diagnostico(request):
    import json
    try:
        data = json.loads(request.body)
        request.session['diagnostico'] = {
            'situacion': data.get('situacion', ''),
            'prevision_actual': data.get('prevision_actual', ''),
            'pago_actual': data.get('pago_actual'),
            'renta': data.get('renta'),
            'cargas': data.get('cargas', ''),
            'clinica': data.get('clinica', ''),
            'preferencia': data.get('preferencia', ''),
            'ahorro_min': data.get('ahorro_min'),
            'ahorro_max': data.get('ahorro_max'),
            'isapres': data.get('isapres', []),
        }
        return JsonResponse({'success': True})
    except Exception:
        return JsonResponse({'success': False}, status=400)
