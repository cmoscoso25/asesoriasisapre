import os
import logging
import requests

logger = logging.getLogger(__name__)


def _fila(label, valor, bold=False, color=None):
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
    api_key = os.environ.get('RESEND_API_KEY', '')
    if not api_key:
        logger.warning(f"RESEND_API_KEY no configurada. Lead #{lead.id} no notificado por email.")
        return

    emails_raw = os.environ.get('ASESOR_EMAILS', 'contacto@asesoriasisapres.com')
    destinatarios = [e.strip() for e in emails_raw.split(',') if e.strip()]

    renta_fmt = f"${lead.renta:,}".replace(',', '.') if lead.renta else "No indicada"
    pago_fmt = f"${lead.pago_actual:,}".replace(',', '.') + "/mes" if lead.pago_actual else "—"
    ahorro_txt = lead.ahorro_display

    prevision_label = lead.get_prevision_actual_display() if lead.prevision_actual else "—"
    preferencia_label = lead.get_preferencia_display() if lead.preferencia else "—"
    edad_txt = f"{lead.edad} años" if lead.edad else "—"
    cargas_txt = lead.get_cargas_display() if lead.cargas else "—"
    clinica_txt = lead.get_clinica_preferente_display() if lead.clinica_preferente else "—"
    situacion_txt = lead.get_situacion_display() if lead.situacion else "—"

    wa_link = (
        f"https://wa.me/569{lead.telefono}"
        f"?text=Hola+{lead.nombre.replace(' ', '+')}%2C+soy+asesor+de"
        f"+Asesor%C3%ADasIsapres.com+y+quiero+ayudarte."
    )

    filas_html = (
        _fila("Nombre", lead.nombre, bold=True) +
        _fila("RUT", f'{lead.rut} <span style="color:#1D9E75;font-size:12px;">&#10003; Verificado</span>') +
        _fila("Celular / WhatsApp",
              f'<a href="{wa_link}" style="color:#0C447C;">'
              f'+569 {lead.telefono}</a>'
              f' <span style="color:#1D9E75;font-size:12px;">&#10003; Verificado</span>') +
        _fila("Email", lead.email or "—") +
        _fila("Edad", edad_txt) +
        _fila("Región", lead.get_region_display() if lead.region else "—") +
        _fila("Situación actual", situacion_txt) +
        _fila("Previsión actual", prevision_label) +
        _fila("Renta imponible", renta_fmt) +
        _fila("Pago actual ISAPRE", pago_fmt) +
        _fila("Preferencia", preferencia_label) +
        _fila("Cargas familiares", cargas_txt) +
        _fila("Clínica preferente", clinica_txt) +
        _fila("Ahorro estimado", ahorro_txt, bold=True, color="#1D9E75") +
        _fila("Origen", f"{lead.utm_source or 'Directo'} / {lead.utm_medium or '—'}") +
        _fila("Fecha/hora", lead.creado.strftime('%d/%m/%Y %H:%M'))
    )

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
      <div style="background:#042C53;padding:20px 24px;border-radius:12px 12px 0 0;">
        <h2 style="color:white;margin:0;font-size:18px;">
          &#128276; Nuevo Lead &mdash; asesoriasisapres.com
        </h2>
        <p style="color:#93C5FD;margin:4px 0 0;font-size:13px;">
          Lead #{lead.id} &bull; {lead.creado.strftime('%d/%m/%Y %H:%M')}
        </p>
      </div>
      <div style="background:#f7f8fa;padding:24px;border-radius:0 0 12px 12px;
                  border:1px solid #e2e8f0;border-top:none;">
        <table style="width:100%;border-collapse:collapse;">
          {filas_html}
        </table>
        <div style="margin-top:24px;display:flex;gap:12px;">
          <a href="{wa_link}"
             style="background:#25D366;color:white;padding:12px 20px;border-radius:8px;
                    text-decoration:none;font-weight:600;display:inline-block;font-size:14px;">
            &#128172; WhatsApp
          </a>
          <a href="mailto:{lead.email}"
             style="background:#0C447C;color:white;padding:12px 20px;border-radius:8px;
                    text-decoration:none;font-weight:600;display:inline-block;font-size:14px;">
            &#128140; Email
          </a>
        </div>
      </div>
    </div>
    """

    from_email = os.environ.get('RESEND_FROM_EMAIL', 'leads@asesoriasisapres.com')
    payload = {
        "from": from_email,
        "to": destinatarios,
        "subject": f"[Lead #{lead.id}] {lead.nombre} — {situacion_txt}",
        "html": html,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=5)
        r.raise_for_status()
        logger.info(f"Lead #{lead.id} notificado a: {destinatarios}")
    except Exception as e:
        logger.error(f"Error enviando email para lead #{lead.id}: {e}")
