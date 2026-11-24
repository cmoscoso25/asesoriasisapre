import os
import logging
from html import escape
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


def _fila(label, valor, bold=False, color=None, es_html=False):
    # Todo valor de usuario se escapa; solo HTML construido aquí usa es_html=True
    if not es_html:
        valor = escape(valor)
    val_style = f"font-weight:{'600' if bold else '400'};font-size:14px;"
    if color:
        val_style += f"color:{color};"
    return (
        f'<tr>'
        f'<td style="padding:8px 0;color:#64748b;font-size:14px;width:42%;'
        f'vertical-align:top;">{label}</td>'
        f'<td style="padding:8px 0;{val_style}">{valor}</td>'
        f'</tr>'
    )


def notificar_asesor(lead):
    import traceback
    try:
        _enviar_notificacion(lead)
    except Exception:
        logger.error(
            "Error inesperado en notificar_asesor lead #%s:\n%s",
            getattr(lead, 'id', '?'),
            traceback.format_exc(),
        )


def _enviar_notificacion(lead):
    api_key = os.environ.get('RESEND_API_KEY', '')
    if not api_key:
        logger.warning("RESEND_API_KEY no configurada. Lead #%s no notificado.", lead.id)
        return

    emails_raw = os.environ.get('ASESOR_EMAILS', 'contacto@asesoriasisapres.com')
    destinatarios = [e.strip() for e in emails_raw.split(',') if e.strip()]
    logger.info("Preparando email lead #%s -> %s", lead.id, destinatarios)

    # Minimización de datos: el email NO incluye RUT ni renta (quedan solo en el
    # CRM, que exige login). El correo pasa por terceros y queda en buzones.
    pago_fmt = f"${lead.pago_actual:,}".replace(',', '.') + "/mes" if lead.pago_actual else "—"
    ahorro_txt = lead.ahorro_display

    prevision_label = lead.get_prevision_actual_display() if lead.prevision_actual else "—"
    preferencia_label = lead.get_preferencia_display() if lead.preferencia else "—"
    edad_txt = f"{lead.edad} años" if lead.edad else "—"
    cargas_txt = lead.get_cargas_display() if lead.cargas else "—"
    clinica_txt = lead.get_clinica_preferente_display() if lead.clinica_preferente else "—"
    situacion_txt = lead.get_situacion_display() if lead.situacion else "—"

    telefono = ''.join(filter(str.isdigit, lead.telefono or ''))
    saludo = 'Hola {}, soy asesor de AsesoríasIsapres.com y quiero ayudarte.'.format(lead.nombre or '')
    # telefono se guarda como 9XXXXXXXX (9 dígitos) → número internacional 56 9XXXXXXXX
    wa_link = escape(f"https://wa.me/56{telefono}?text={quote(saludo)}")
    email_link = escape(f"mailto:{quote(lead.email or '', safe='@')}")

    # Resultado de la sincronización con el CRM (gestion/signals.py)
    crm_resultado = getattr(lead, '_crm_resultado', '')
    prospecto = getattr(lead, '_crm_prospecto', None) or getattr(lead, 'prospecto', None)
    crm_url = (f"https://asesoriasisapres.com/gestion/prospectos/{prospecto.pk}/"
               if prospecto else f"https://asesoriasisapres.com/gestion-interna/leads/lead/{lead.pk}/change/")
    if crm_resultado == 'error':
        aviso_crm = ('#FEE2E2', '#991B1B',
                     '⚠️ No se pudo crear la ficha en el CRM. Revisa el lead en el admin y créala manualmente.')
    elif crm_resultado == 'existente':
        aviso_crm = ('#FEF3C7', '#92400E',
                     '🔁 Contacto repetido: esta persona ya estaba en el CRM. Se agregó una nota a su ficha '
                     'y quedó con prioridad Alta y seguimiento para hoy.')
    else:
        aviso_crm = None
    aviso_html = (
        f'<div style="background:{aviso_crm[0]};color:{aviso_crm[1]};padding:12px 16px;border-radius:8px;'
        f'font-size:14px;margin-bottom:16px;">{escape(aviso_crm[2])}</div>'
        if aviso_crm else ''
    )

    fecha_txt = lead.creado.strftime('%d/%m/%Y %H:%M') if lead.creado else "—"

    filas_html = (
        _fila("Nombre", lead.nombre, bold=True) +
        _fila("Celular / WhatsApp",
              f'<a href="{wa_link}" style="color:#0C447C;">'
              f'+56 {escape(telefono)}</a>'
              f' <span style="color:#1D9E75;font-size:12px;">&#10003; Verificado</span>',
              es_html=True) +
        _fila("Email", lead.email or "—") +
        _fila("Edad", edad_txt) +
        _fila("Región", lead.get_region_display() if lead.region else "—") +
        _fila("Situación actual", situacion_txt) +
        _fila("Previsión actual", prevision_label) +
        _fila("Pago actual ISAPRE", pago_fmt) +
        _fila("Preferencia", preferencia_label) +
        _fila("Cargas familiares", cargas_txt) +
        _fila("Clínica preferente", clinica_txt) +
        _fila("Ahorro estimado", ahorro_txt, bold=True, color="#1D9E75") +
        _fila("Origen", f"{lead.utm_source or 'Directo'} / {lead.utm_medium or '—'}") +
        _fila("Fecha/hora", fecha_txt)
    )

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
      <div style="background:#042C53;padding:20px 24px;border-radius:12px 12px 0 0;">
        <h2 style="color:white;margin:0;font-size:18px;">
          &#128276; Nuevo Lead &mdash; asesoriasisapres.com
        </h2>
        <p style="color:#93C5FD;margin:4px 0 0;font-size:13px;">
          Lead #{lead.id} &bull; {fecha_txt}
        </p>
      </div>
      <div style="background:#f7f8fa;padding:24px;border-radius:0 0 12px 12px;
                  border:1px solid #e2e8f0;border-top:none;">
        {aviso_html}
        <table style="width:100%;border-collapse:collapse;">
          {filas_html}
        </table>
        <div style="margin-top:24px;display:flex;gap:12px;">
          <a href="{wa_link}"
             style="background:#25D366;color:white;padding:12px 20px;border-radius:8px;
                    text-decoration:none;font-weight:600;display:inline-block;font-size:14px;">
            &#128172; WhatsApp
          </a>
          <a href="{email_link}"
             style="background:#0C447C;color:white;padding:12px 20px;border-radius:8px;
                    text-decoration:none;font-weight:600;display:inline-block;font-size:14px;">
            &#128140; Email
          </a>
        </div>
        <p style="margin-top:20px;font-size:13px;color:#64748b;">
          RUT, renta y diagnóstico completo en el CRM (requiere iniciar sesión):<br>
          <a href="{escape(crm_url)}" style="color:#0C447C;">Ver ficha del prospecto &rarr;</a>
        </p>
      </div>
    </div>
    """

    from_email = os.environ.get('RESEND_FROM_EMAIL', 'leads@asesoriasisapres.com')
    payload = {
        "from": from_email,
        "to": destinatarios,
        "subject": (
            ("⚠️ SIN FICHA CRM · " if crm_resultado == 'error' else
             "🔁 Repetido · " if crm_resultado == 'existente' else "")
            + f"[Lead #{lead.id}] {lead.nombre} — {situacion_txt}"
        ),
        "html": html,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=8)
        r.raise_for_status()
        logger.info("Lead #%s notificado OK (status %s)", lead.id, r.status_code)
    except Exception as e:
        logger.error("Error Resend para lead #%s: %s", lead.id, e)
