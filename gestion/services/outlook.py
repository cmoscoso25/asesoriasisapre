"""
Microsoft Graph / Outlook Calendar integration.

Requires env vars:
    MICROSOFT_CLIENT_ID
    MICROSOFT_CLIENT_SECRET
    MICROSOFT_TENANT_ID  (use 'common' for multi-tenant)
    MICROSOFT_REDIRECT_URI  (e.g. https://asesoriasisapres.com/gestion/outlook/callback/)
"""
import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('gestion')

SCOPES = ['Calendars.ReadWrite', 'User.Read', 'offline_access']
GRAPH_BASE = 'https://graph.microsoft.com/v1.0'


class OutlookError(Exception):
    pass


class OutlookAuthError(OutlookError):
    pass


def _msal_app():
    try:
        import msal
    except ImportError:
        raise OutlookError(
            "El paquete 'msal' no está instalado. "
            "Ejecuta: pip install msal>=1.31.0"
        )

    client_id = getattr(settings, 'MICROSOFT_CLIENT_ID', '')
    client_secret = getattr(settings, 'MICROSOFT_CLIENT_SECRET', '')
    tenant_id = getattr(settings, 'MICROSOFT_TENANT_ID', 'common')

    if not client_id or not client_secret:
        raise OutlookError(
            "MICROSOFT_CLIENT_ID y MICROSOFT_CLIENT_SECRET son requeridos."
        )

    return msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
    )


def iniciar_flujo_oauth(request):
    """
    Inicia el flujo OAuth 2.0 Authorization Code.
    Devuelve el dict flow que se debe guardar en la sesión.
    """
    app = _msal_app()
    redirect_uri = getattr(settings, 'MICROSOFT_REDIRECT_URI', '')
    flow = app.initiate_auth_code_flow(
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    return flow


def completar_flujo_oauth(flow, auth_response):
    """
    Intercambia el código de autorización por tokens.
    Devuelve un dict con access_token, refresh_token, expires_in.
    Lanza OutlookAuthError si falla.
    """
    app = _msal_app()
    result = app.acquire_token_by_auth_code_flow(flow, auth_response)
    if 'error' in result:
        raise OutlookAuthError(
            result.get('error_description', result.get('error', 'Error desconocido'))
        )
    return result


def obtener_token_valido(conexion):
    """
    Devuelve un access token válido, refrescándolo si ha expirado.
    Actualiza la conexion en la DB si se refresca.
    Lanza OutlookAuthError si el refresh falla.
    """
    now = timezone.now()
    if conexion.token_expires_at and now < conexion.token_expires_at - timedelta(minutes=5):
        return conexion.access_token

    # Token expirado — refrescar
    app = _msal_app()
    result = app.acquire_token_by_refresh_token(
        refresh_token=conexion.refresh_token,
        scopes=SCOPES,
    )
    if 'error' in result:
        conexion.conectado = False
        conexion.save(update_fields=['conectado'])
        raise OutlookAuthError(
            result.get('error_description', 'Error al refrescar token')
        )

    conexion.access_token = result['access_token']
    if 'refresh_token' in result:
        conexion.refresh_token = result['refresh_token']
    expires_in = result.get('expires_in', 3600)
    conexion.token_expires_at = now + timedelta(seconds=expires_in)
    conexion.save(update_fields=['access_token', 'refresh_token', 'token_expires_at'])
    return conexion.access_token


def obtener_perfil(conexion):
    """Devuelve el perfil del usuario autenticado en Microsoft."""
    token = obtener_token_valido(conexion)
    resp = requests.get(
        f'{GRAPH_BASE}/me',
        headers={'Authorization': f'Bearer {token}'},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def crear_evento_outlook(conexion, reunion):
    """
    Crea un evento en el calendario de Outlook del usuario.
    Devuelve el event_id de Graph API.
    """
    from datetime import datetime, time as dt_time
    token = obtener_token_valido(conexion)

    fecha_str = reunion.fecha.strftime('%Y-%m-%d')
    inicio = f"{fecha_str}T{reunion.hora_inicio.strftime('%H:%M:%S')}"
    if reunion.hora_fin:
        fin = f"{fecha_str}T{reunion.hora_fin.strftime('%H:%M:%S')}"
    else:
        # Default +1 hora
        from datetime import datetime as dt
        hora_fin = (dt.combine(reunion.fecha, reunion.hora_inicio) + timedelta(hours=1)).time()
        fin = f"{fecha_str}T{hora_fin.strftime('%H:%M:%S')}"

    body = {
        'subject': reunion.titulo,
        'body': {
            'contentType': 'Text',
            'content': reunion.descripcion or '',
        },
        'start': {'dateTime': inicio, 'timeZone': 'America/Santiago'},
        'end':   {'dateTime': fin,    'timeZone': 'America/Santiago'},
        'location': {'displayName': reunion.ubicacion or ''},
        'reminderMinutesBeforeStart': reunion.recordatorio_minutos,
        'isReminderOn': True,
    }

    resp = requests.post(
        f'{GRAPH_BASE}/me/events',
        json=body,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return data['id']


def actualizar_evento_outlook(conexion, reunion):
    """Actualiza un evento existente en Outlook."""
    if not reunion.outlook_event_id:
        return crear_evento_outlook(conexion, reunion)

    token = obtener_token_valido(conexion)
    fecha_str = reunion.fecha.strftime('%Y-%m-%d')
    inicio = f"{fecha_str}T{reunion.hora_inicio.strftime('%H:%M:%S')}"
    if reunion.hora_fin:
        fin = f"{fecha_str}T{reunion.hora_fin.strftime('%H:%M:%S')}"
    else:
        from datetime import datetime as dt
        hora_fin = (dt.combine(reunion.fecha, reunion.hora_inicio) + timedelta(hours=1)).time()
        fin = f"{fecha_str}T{hora_fin.strftime('%H:%M:%S')}"

    body = {
        'subject': reunion.titulo,
        'start': {'dateTime': inicio, 'timeZone': 'America/Santiago'},
        'end':   {'dateTime': fin,    'timeZone': 'America/Santiago'},
        'location': {'displayName': reunion.ubicacion or ''},
    }

    resp = requests.patch(
        f'{GRAPH_BASE}/me/events/{reunion.outlook_event_id}',
        json=body,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
        timeout=15,
    )
    resp.raise_for_status()


def eliminar_evento_outlook(conexion, event_id):
    """Elimina un evento de Outlook."""
    token = obtener_token_valido(conexion)
    resp = requests.delete(
        f'{GRAPH_BASE}/me/events/{event_id}',
        headers={'Authorization': f'Bearer {token}'},
        timeout=10,
    )
    if resp.status_code not in (204, 404):
        resp.raise_for_status()
