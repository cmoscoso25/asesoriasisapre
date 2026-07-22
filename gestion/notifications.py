import logging
import os
import urllib.parse
import urllib.request

import requests

logger = logging.getLogger('gestion')


def enviar_email_recordatorio(reunion):
    api_key = os.environ.get('RESEND_API_KEY', '')
    if not api_key:
        logger.warning("RESEND_API_KEY no configurada, no se envió email de recordatorio.")
        return False

    emails_raw = os.environ.get('ASESOR_EMAILS', '')
    destinatarios = [e.strip() for e in emails_raw.split(',') if e.strip()]
    if not destinatarios:
        logger.warning("ASESOR_EMAILS no configurado.")
        return False

    from_email = os.environ.get('RESEND_FROM_EMAIL', 'notificaciones@asesoriasisapres.com')
    prospecto = reunion.prospecto
    hora = reunion.hora_inicio.strftime('%H:%M')
    modalidad = reunion.get_modalidad_display()
    ubicacion_fila = (
        f'<tr><td style="padding:8px 0;color:#64748b;font-size:14px;width:40%;">Ubicación / Enlace</td>'
        f'<td style="padding:8px 0;font-size:14px;">{reunion.ubicacion}</td></tr>'
        if reunion.ubicacion else ''
    )

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f7f8fa;padding:24px;">
      <div style="background:#042C53;padding:16px 24px;border-radius:8px 8px 0 0;">
        <h1 style="color:#fff;font-size:18px;margin:0;">&#9200; Recordatorio de Reunión — 15 min</h1>
      </div>
      <div style="background:#fff;padding:24px;border-radius:0 0 8px 8px;border:1px solid #e2e8f0;">
        <p style="font-size:15px;color:#0C447C;font-weight:600;margin-top:0;">
          Tienes una reunión en aproximadamente 15 minutos.
        </p>
        <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
          <tr>
            <td style="padding:8px 0;color:#64748b;font-size:14px;width:40%;">Prospecto</td>
            <td style="padding:8px 0;font-size:14px;font-weight:600;">{prospecto.nombre}</td>
          </tr>
          <tr>
            <td style="padding:8px 0;color:#64748b;font-size:14px;">Teléfono</td>
            <td style="padding:8px 0;font-size:14px;">{prospecto.telefono}</td>
          </tr>
          <tr>
            <td style="padding:8px 0;color:#64748b;font-size:14px;">Reunión</td>
            <td style="padding:8px 0;font-size:14px;font-weight:600;">{reunion.titulo}</td>
          </tr>
          <tr>
            <td style="padding:8px 0;color:#64748b;font-size:14px;">Hora</td>
            <td style="padding:8px 0;font-size:14px;font-weight:600;">{hora}</td>
          </tr>
          <tr>
            <td style="padding:8px 0;color:#64748b;font-size:14px;">Modalidad</td>
            <td style="padding:8px 0;font-size:14px;">{modalidad}</td>
          </tr>
          {ubicacion_fila}
        </table>
        <a href="https://asesoriasisapres.com/gestion/reuniones/"
           style="display:inline-block;background:#1D9E75;color:#fff;padding:10px 20px;
                  border-radius:6px;text-decoration:none;font-size:14px;font-weight:600;">
          Ver en CRM
        </a>
      </div>
      <p style="font-size:12px;color:#94a3b8;text-align:center;margin-top:16px;">
        AsesoríasIsapres — notificación automática
      </p>
    </div>
    """

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'from': from_email,
        'to': destinatarios,
        'subject': f'⏰ Reunión en 15 min: {reunion.titulo} con {prospecto.nombre}',
        'html': html,
    }

    try:
        r = requests.post('https://api.resend.com/emails', json=payload, headers=headers, timeout=8)
        r.raise_for_status()
        logger.info("Email recordatorio enviado: reunión #%s", reunion.pk)
        return True
    except Exception as exc:
        logger.error("Error email recordatorio reunión #%s: %s", reunion.pk, exc)
        return False


def enviar_whatsapp_recordatorio(reunion):
    phone = os.environ.get('CALLMEBOT_PHONE', '')
    apikey = os.environ.get('CALLMEBOT_APIKEY', '')
    if not phone or not apikey:
        logger.warning("CALLMEBOT_PHONE o CALLMEBOT_APIKEY no configurados.")
        return False

    hora = reunion.hora_inicio.strftime('%H:%M')
    prospecto = reunion.prospecto
    partes = [
        f"⏰ *Recordatorio AsesoríasIsapres*",
        f"Reunión en ~15 minutos:",
        f"\U0001f464 {prospecto.nombre}  |  {prospecto.telefono}",
        f"\U0001f4cb {reunion.titulo}",
        f"\U0001f550 {hora}  —  {reunion.get_modalidad_display()}",
    ]
    if reunion.ubicacion:
        partes.append(f"\U0001f4cd {reunion.ubicacion}")

    mensaje = '\n'.join(partes)
    encoded = urllib.parse.quote(mensaje)
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded}&apikey={apikey}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            logger.info("WhatsApp recordatorio enviado: reunión #%s (HTTP %s)", reunion.pk, resp.status)
        return True
    except Exception as exc:
        logger.error("Error WhatsApp recordatorio reunión #%s: %s", reunion.pk, exc)
        return False
