import json
import logging
from datetime import date, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import GestionForm, ProspectoForm, ReunionForm, TareaForm
from .models import (
    ConexionOutlook, GestionProspecto, Prospecto, Reunion, TareaSeguimiento,
)

logger = logging.getLogger('gestion')

LOGIN_URL = '/gestion-interna/login/'


# ---------------------------------------------------------------------------
# Decorador de acceso
# ---------------------------------------------------------------------------

def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path(), LOGIN_URL)
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped


def _ctx_base(request):
    """Contexto común para todas las vistas de gestión."""
    today = date.today()
    return {
        'tareas_vencidas_count': TareaSeguimiento.objects.filter(
            estado='pendiente', fecha__lt=today,
        ).count(),
        'reuniones_hoy_count': Reunion.objects.filter(
            fecha=today, estado__in=('agendada', 'confirmada'),
        ).count(),
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@staff_required
def dashboard(request):
    today = date.today()
    semana_inicio = today - timedelta(days=today.weekday())

    reuniones_hoy = Reunion.objects.filter(
        fecha=today, estado__in=('agendada', 'confirmada'),
    ).select_related('prospecto').order_by('hora_inicio')

    tareas_hoy = TareaSeguimiento.objects.filter(
        fecha=today, estado='pendiente',
    ).select_related('prospecto').order_by('hora')

    tareas_vencidas = TareaSeguimiento.objects.filter(
        estado='pendiente', fecha__lt=today,
    ).select_related('prospecto').order_by('fecha')[:10]

    nuevos_esta_semana = Prospecto.objects.filter(
        activo=True, creado__date__gte=semana_inicio,
    ).count()

    pipeline = {
        row['estado']: row['total']
        for row in Prospecto.objects.filter(activo=True)
        .values('estado')
        .annotate(total=Count('id'))
    }

    ventas_mes = Prospecto.objects.filter(
        estado='venta',
        actualizado__month=today.month,
        actualizado__year=today.year,
    ).count()

    proximos_7_dias = Reunion.objects.filter(
        fecha__gte=today,
        fecha__lte=today + timedelta(days=7),
        estado__in=('agendada', 'confirmada'),
    ).select_related('prospecto').order_by('fecha', 'hora_inicio')[:8]

    ctx = _ctx_base(request)
    estados_label = dict(Prospecto.ESTADO_CHOICES)
    ctx.update({
        'reuniones_hoy':      reuniones_hoy,
        'tareas_hoy':         tareas_hoy,
        'tareas_vencidas':    tareas_vencidas,
        'nuevos_esta_semana': nuevos_esta_semana,
        'pipeline':           pipeline,
        'ventas_mes':         ventas_mes,
        'proximos_7_dias':    proximos_7_dias,
        'estados_label':      estados_label,
    })
    return render(request, 'gestion/dashboard.html', ctx)


# ---------------------------------------------------------------------------
# Prospectos
# ---------------------------------------------------------------------------

@staff_required
def prospecto_lista(request):
    qs = Prospecto.objects.filter(activo=True).select_related('responsable')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(nombre__icontains=q) | Q(telefono__icontains=q) | Q(email__icontains=q)
        )

    estado = request.GET.get('estado', '')
    if estado:
        qs = qs.filter(estado=estado)

    prioridad = request.GET.get('prioridad', '')
    if prioridad:
        qs = qs.filter(prioridad=prioridad)

    paginator = Paginator(qs, 25)
    page_obj  = paginator.get_page(request.GET.get('page'))

    ctx = _ctx_base(request)
    ctx.update({
        'page_obj':        page_obj,
        'q':               q,
        'filtro_estado':   estado,
        'filtro_prioridad':prioridad,
        'estado_choices':  Prospecto.ESTADO_CHOICES,
        'prioridad_choices': Prospecto.PRIORIDAD_CHOICES,
        'estados_color':   Prospecto.ESTADO_COLOR,
    })
    return render(request, 'gestion/prospectos/lista.html', ctx)


@staff_required
def prospecto_nuevo(request):
    form = ProspectoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        p = form.save(commit=False)
        if not p.responsable:
            p.responsable = request.user
        p.save()
        messages.success(request, f'Prospecto «{p.nombre}» creado correctamente.')
        return redirect('gestion:prospecto_detalle', pk=p.pk)

    ctx = _ctx_base(request)
    ctx.update({'form': form, 'titulo': 'Nuevo prospecto'})
    return render(request, 'gestion/prospectos/form.html', ctx)


@staff_required
def prospecto_detalle(request, pk):
    prospecto = get_object_or_404(Prospecto, pk=pk)
    gestiones = prospecto.gestiones.select_related('usuario').all()
    reuniones = prospecto.reuniones.all()
    tareas    = prospecto.tareas.all()

    gestion_form = GestionForm()

    ctx = _ctx_base(request)
    ctx.update({
        'prospecto':    prospecto,
        'gestiones':    gestiones,
        'reuniones':    reuniones,
        'tareas':       tareas,
        'gestion_form': gestion_form,
        'estados':      Prospecto.ESTADO_CHOICES,
    })
    return render(request, 'gestion/prospectos/detalle.html', ctx)


@staff_required
def prospecto_editar(request, pk):
    prospecto = get_object_or_404(Prospecto, pk=pk)
    form = ProspectoForm(request.POST or None, instance=prospecto)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Prospecto actualizado.')
        return redirect('gestion:prospecto_detalle', pk=pk)

    ctx = _ctx_base(request)
    ctx.update({'form': form, 'prospecto': prospecto, 'titulo': f'Editar — {prospecto.nombre}'})
    return render(request, 'gestion/prospectos/form.html', ctx)


@staff_required
@require_POST
def prospecto_archivar(request, pk):
    prospecto = get_object_or_404(Prospecto, pk=pk)
    prospecto.activo = False
    prospecto.save(update_fields=['activo'])
    messages.success(request, f'Prospecto «{prospecto.nombre}» archivado.')
    return redirect('gestion:prospecto_lista')


@staff_required
@require_POST
def prospecto_cambiar_estado(request, pk):
    prospecto = get_object_or_404(Prospecto, pk=pk)
    nuevo_estado = request.POST.get('estado', '')
    estados_validos = [e[0] for e in Prospecto.ESTADO_CHOICES]
    if nuevo_estado in estados_validos:
        prospecto.estado = nuevo_estado
        prospecto.save(update_fields=['estado', 'actualizado'])
        # Registrar en historial
        GestionProspecto.objects.create(
            prospecto=prospecto,
            usuario=request.user,
            tipo='estado',
            descripcion=f'Estado cambiado a: {dict(Prospecto.ESTADO_CHOICES)[nuevo_estado]}',
        )
        messages.success(request, f'Estado actualizado a «{dict(Prospecto.ESTADO_CHOICES)[nuevo_estado]}».')
    return redirect('gestion:prospecto_detalle', pk=pk)


# ---------------------------------------------------------------------------
# Gestiones (timeline de actividades)
# ---------------------------------------------------------------------------

@staff_required
@require_POST
def gestion_nueva(request, prospecto_pk):
    prospecto = get_object_or_404(Prospecto, pk=prospecto_pk)
    form = GestionForm(request.POST)
    if form.is_valid():
        g = form.save(commit=False)
        g.prospecto = prospecto
        g.usuario   = request.user
        g.save()
        # Actualizar próximo seguimiento en el prospecto si se indicó
        if g.fecha_proxima_accion:
            prospecto.proximo_seguimiento = g.fecha_proxima_accion
            prospecto.save(update_fields=['proximo_seguimiento', 'actualizado'])
        messages.success(request, 'Gestión registrada.')
    else:
        messages.error(request, 'Error al guardar la gestión. Verifica los datos.')
    return redirect('gestion:prospecto_detalle', pk=prospecto_pk)


# ---------------------------------------------------------------------------
# Reuniones
# ---------------------------------------------------------------------------

@staff_required
def reunion_lista(request):
    qs = Reunion.objects.select_related('prospecto').all()

    estado = request.GET.get('estado', '')
    if estado:
        qs = qs.filter(estado=estado)

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(titulo__icontains=q) | Q(prospecto__nombre__icontains=q)
        )

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))

    ctx = _ctx_base(request)
    ctx.update({
        'page_obj':      page_obj,
        'estado_choices':Reunion.ESTADO_CHOICES,
        'filtro_estado': estado,
        'q':             q,
    })
    return render(request, 'gestion/reuniones/lista.html', ctx)


@staff_required
def reunion_nueva(request):
    prospecto_pk = request.GET.get('prospecto') or request.POST.get('prospecto')
    qs_prospectos = Prospecto.objects.filter(activo=True).order_by('nombre')

    initial = {}
    if prospecto_pk:
        initial['prospecto'] = prospecto_pk

    form = ReunionForm(
        request.POST or None,
        initial=initial,
        prospecto_queryset=qs_prospectos,
    )
    if request.method == 'POST' and form.is_valid():
        reunion = form.save(commit=False)
        if not reunion.responsable:
            reunion.responsable = request.user
        reunion.save()
        _sincronizar_outlook(request, reunion)
        messages.success(request, f'Reunión «{reunion.titulo}» agendada.')
        return redirect('gestion:prospecto_detalle', pk=reunion.prospecto.pk)

    ctx = _ctx_base(request)
    ctx.update({'form': form, 'titulo': 'Nueva reunión'})
    return render(request, 'gestion/reuniones/form.html', ctx)


@staff_required
def reunion_editar(request, pk):
    reunion = get_object_or_404(Reunion, pk=pk)
    qs_prospectos = Prospecto.objects.filter(activo=True).order_by('nombre')
    form = ReunionForm(request.POST or None, instance=reunion, prospecto_queryset=qs_prospectos)
    if request.method == 'POST' and form.is_valid():
        r = form.save()
        _sincronizar_outlook(request, r, update=True)
        messages.success(request, 'Reunión actualizada.')
        return redirect('gestion:prospecto_detalle', pk=r.prospecto.pk)

    ctx = _ctx_base(request)
    ctx.update({'form': form, 'reunion': reunion, 'titulo': f'Editar reunión — {reunion.titulo}'})
    return render(request, 'gestion/reuniones/form.html', ctx)


@staff_required
@require_POST
def reunion_cancelar(request, pk):
    reunion = get_object_or_404(Reunion, pk=pk)
    reunion.estado = 'cancelada'
    reunion.save(update_fields=['estado', 'actualizado'])
    messages.success(request, 'Reunión cancelada.')
    return redirect('gestion:prospecto_detalle', pk=reunion.prospecto.pk)


def _sincronizar_outlook(request, reunion, update=False):
    """Intenta sincronizar la reunión con Outlook si el usuario está conectado."""
    try:
        conexion = request.user.conexion_outlook
        if not conexion.conectado:
            return
        from gestion.services.outlook import (
            actualizar_evento_outlook, crear_evento_outlook, OutlookError,
        )
        if update and reunion.outlook_event_id:
            actualizar_evento_outlook(conexion, reunion)
        else:
            event_id = crear_evento_outlook(conexion, reunion)
            reunion.outlook_event_id = event_id
            reunion.outlook_sync_at  = timezone.now()
            reunion.save(update_fields=['outlook_event_id', 'outlook_sync_at'])
    except ConexionOutlook.DoesNotExist:
        pass
    except Exception as exc:
        logger.warning("No se pudo sincronizar con Outlook: %s", exc)
        messages.warning(request, f'Reunión guardada, pero no se pudo sincronizar con Outlook: {exc}')


# ---------------------------------------------------------------------------
# Tareas
# ---------------------------------------------------------------------------

@staff_required
def tarea_lista(request):
    qs = TareaSeguimiento.objects.filter(
        estado__in=('pendiente', 'proceso'),
    ).select_related('prospecto').order_by('fecha', 'hora')

    today = date.today()
    tareas_hoy      = qs.filter(fecha=today)
    tareas_vencidas = qs.filter(fecha__lt=today)
    tareas_proximas = qs.filter(fecha__gt=today, fecha__lte=today + timedelta(days=7))

    ctx = _ctx_base(request)
    ctx.update({
        'tareas_hoy':      tareas_hoy,
        'tareas_vencidas': tareas_vencidas,
        'tareas_proximas': tareas_proximas,
        'today':           today,
    })
    return render(request, 'gestion/tareas/lista.html', ctx)


@staff_required
def tarea_nueva(request):
    prospecto_pk = request.GET.get('prospecto') or request.POST.get('prospecto')
    qs = Prospecto.objects.filter(activo=True).order_by('nombre')
    initial = {}
    if prospecto_pk:
        initial['prospecto'] = prospecto_pk

    form = TareaForm(request.POST or None, initial=initial, prospecto_queryset=qs)
    if request.method == 'POST' and form.is_valid():
        t = form.save(commit=False)
        if not t.responsable:
            t.responsable = request.user
        t.save()
        messages.success(request, 'Tarea creada.')
        return redirect('gestion:prospecto_detalle', pk=t.prospecto.pk)

    ctx = _ctx_base(request)
    ctx.update({'form': form, 'titulo': 'Nueva tarea'})
    return render(request, 'gestion/tareas/form.html', ctx)


@staff_required
def tarea_editar(request, pk):
    tarea = get_object_or_404(TareaSeguimiento, pk=pk)
    qs = Prospecto.objects.filter(activo=True).order_by('nombre')
    form = TareaForm(request.POST or None, instance=tarea, prospecto_queryset=qs)
    if request.method == 'POST' and form.is_valid():
        t = form.save()
        messages.success(request, 'Tarea actualizada.')
        return redirect('gestion:prospecto_detalle', pk=t.prospecto.pk)

    ctx = _ctx_base(request)
    ctx.update({'form': form, 'tarea': tarea, 'titulo': f'Editar tarea — {tarea.titulo}'})
    return render(request, 'gestion/tareas/form.html', ctx)


@staff_required
@require_POST
def tarea_completar(request, pk):
    tarea = get_object_or_404(TareaSeguimiento, pk=pk)
    tarea.estado          = 'completada'
    tarea.fecha_completada= timezone.now()
    tarea.save(update_fields=['estado', 'fecha_completada', 'actualizado'])
    messages.success(request, f'Tarea «{tarea.titulo}» marcada como completada.')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'gestion:tarea_lista'
    if next_url.startswith('/'):
        return redirect(next_url)
    return redirect('gestion:tarea_lista')


@staff_required
@require_POST
def tarea_cancelar(request, pk):
    tarea = get_object_or_404(TareaSeguimiento, pk=pk)
    tarea.estado = 'cancelada'
    tarea.save(update_fields=['estado', 'actualizado'])
    messages.success(request, 'Tarea cancelada.')
    return redirect('gestion:prospecto_detalle', pk=tarea.prospecto.pk)


# ---------------------------------------------------------------------------
# Calendario
# ---------------------------------------------------------------------------

@staff_required
def calendario(request):
    ctx = _ctx_base(request)
    return render(request, 'gestion/calendario.html', ctx)


@staff_required
def calendario_eventos(request):
    """JSON: eventos para el calendario vanilla JS."""
    inicio_str = request.GET.get('inicio', '')
    fin_str    = request.GET.get('fin', '')

    qs = Reunion.objects.select_related('prospecto').all()
    if inicio_str:
        try:
            from datetime import datetime
            inicio = datetime.strptime(inicio_str, '%Y-%m-%d').date()
            qs = qs.filter(fecha__gte=inicio)
        except ValueError:
            pass
    if fin_str:
        try:
            from datetime import datetime
            fin = datetime.strptime(fin_str, '%Y-%m-%d').date()
            qs = qs.filter(fecha__lte=fin)
        except ValueError:
            pass

    COLOR_MAP = {
        'agendada':     '#185FA5',
        'confirmada':   '#1D9E75',
        'realizada':    '#0F6E56',
        'cancelada':    '#ef4444',
        'reprogramada': '#d97706',
        'no_asistio':   '#9ca3af',
    }

    eventos = []
    for r in qs:
        eventos.append({
            'id':      r.pk,
            'title':   r.titulo,
            'start':   f"{r.fecha}T{r.hora_inicio}",
            'end':     f"{r.fecha}T{r.hora_fin}" if r.hora_fin else None,
            'color':   COLOR_MAP.get(r.estado, '#185FA5'),
            'estado':  r.estado,
            'url':     f'/gestion/reuniones/{r.pk}/editar/',
            'prospecto': r.prospecto.nombre,
        })
    return JsonResponse(eventos, safe=False)


# ---------------------------------------------------------------------------
# Outlook OAuth
# ---------------------------------------------------------------------------

@staff_required
def outlook_estado(request):
    conexion = None
    try:
        conexion = request.user.conexion_outlook
    except ConexionOutlook.DoesNotExist:
        pass

    outlook_configurado = bool(
        getattr(request, 'MICROSOFT_CLIENT_ID', '') or
        __import__('django.conf', fromlist=['settings']).settings.__dict__.get('MICROSOFT_CLIENT_ID') or
        __import__('os').environ.get('MICROSOFT_CLIENT_ID')
    )

    ctx = _ctx_base(request)
    ctx.update({
        'conexion': conexion,
        'outlook_configurado': bool(__import__('os').environ.get('MICROSOFT_CLIENT_ID')),
    })
    return render(request, 'gestion/outlook/estado.html', ctx)


@staff_required
def outlook_conectar(request):
    import os
    if not os.environ.get('MICROSOFT_CLIENT_ID'):
        messages.error(request, 'Microsoft OAuth no está configurado. Revisa las variables de entorno.')
        return redirect('gestion:outlook_estado')

    from gestion.services.outlook import OutlookError, iniciar_flujo_oauth
    try:
        flow = iniciar_flujo_oauth(request)
        request.session['outlook_flow'] = flow
        return redirect(flow['auth_uri'])
    except OutlookError as exc:
        messages.error(request, f'Error al iniciar conexión con Outlook: {exc}')
        return redirect('gestion:outlook_estado')


@staff_required
def outlook_callback(request):
    from gestion.services.outlook import OutlookAuthError, OutlookError, completar_flujo_oauth, obtener_perfil

    flow = request.session.pop('outlook_flow', None)
    if not flow:
        messages.error(request, 'Sesión OAuth expirada. Intenta conectarte de nuevo.')
        return redirect('gestion:outlook_estado')

    auth_response = {
        'code':  request.GET.get('code', ''),
        'state': request.GET.get('state', ''),
    }

    try:
        result = completar_flujo_oauth(flow, auth_response)
    except OutlookAuthError as exc:
        messages.error(request, f'Error de autenticación con Microsoft: {exc}')
        return redirect('gestion:outlook_estado')

    from datetime import timedelta
    expires_at = timezone.now() + timedelta(seconds=result.get('expires_in', 3600))

    conexion, _ = ConexionOutlook.objects.get_or_create(usuario=request.user)
    conexion.access_token     = result['access_token']
    conexion.refresh_token    = result.get('refresh_token', '')
    conexion.token_expires_at = expires_at
    conexion.conectado        = True
    conexion.save()

    # Obtener perfil
    try:
        perfil = obtener_perfil(conexion)
        conexion.email         = perfil.get('mail') or perfil.get('userPrincipalName', '')
        conexion.nombre_cuenta = perfil.get('displayName', '')
        conexion.save(update_fields=['email', 'nombre_cuenta'])
    except Exception as exc:
        logger.warning("No se pudo obtener perfil de Outlook: %s", exc)

    messages.success(request, f'Outlook conectado correctamente ({conexion.email}).')
    return redirect('gestion:outlook_estado')


@staff_required
@require_POST
def outlook_desconectar(request):
    try:
        conexion = request.user.conexion_outlook
        conexion.delete()
        messages.success(request, 'Conexión con Outlook eliminada.')
    except ConexionOutlook.DoesNotExist:
        messages.info(request, 'No había conexión con Outlook.')
    return redirect('gestion:outlook_estado')
