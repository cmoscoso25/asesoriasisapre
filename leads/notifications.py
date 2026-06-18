import os
import logging
import requests

logger = logging.getLogger(__name__)

def notificar_asesor(lead):
    api_key = os.environ.get('RESEND_API_KEY', '')
    if not api_key:
        logger.warning(f"RESEND_API_KEY no configurada. Lead #{lead.id} no notificado por email.")
        return

    ahorro_txt = lead.ahorro_display
    renta_fmt = f"${lead.renta:,}".replace(',', '.') if lead.renta else "No indicada"

    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
      <div style="background:#042C53;padding:20px 24px;border-radius:12px 12px 0 0;">
        <h2 style="color:white;margin:0;font-size:18px;">
          &#128276; Nuevo Lead — asesoriasisapres.com
        </h2>
      </div>
      <div style="background:#f7f8fa;padding:24px;border-radius:0 0 12px 12px;
                  border:1px solid #e2e8f0;border-top:none;">
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:8px 0;color:#64748b;font-size:14px;width:40%;">Nombre</td>
              <td style="padding:8px 0;font-weight:600;font-size:14px;">{lead.nombre}</td></tr>
          <tr><td style="padding:8px 0;color:#64748b;font-size:14px;">Teléfono</td>
              <td style="padding:8px 0;font-weight:600;font-size:14px;">
                <a href="tel:+569{lead.telefono}" style="color:#0C447C;">+569 {lead.telefono}</a>
              </td></tr>
          <tr><td style="padding:8px 0;color:#64748b;font-size:14px;">Email</td>
              <td style="padding:8px 0;font-size:14px;">{lead.email or '—'}</td></tr>
          <tr><td style="padding:8px 0;color:#64748b;font-size:14px;">Situación</td>
              <td style="padding:8px 0;font-size:14px;">{lead.get_situacion_display()}</td></tr>
          <tr><td style="padding:8px 0;color:#64748b;font-size:14px;">Renta imponible</td>
              <td style="padding:8px 0;font-size:14px;">{renta_fmt}</td></tr>
          <tr><td style="padding:8px 0;color:#64748b;font-size:14px;">Cargas</td>
              <td style="padding:8px 0;font-size:14px;">{lead.get_cargas_display() if lead.cargas else '—'}</td></tr>
          <tr><td style="padding:8px 0;color:#64748b;font-size:14px;">Clínica preferente</td>
              <td style="padding:8px 0;font-size:14px;">{lead.get_clinica_preferente_display() if lead.clinica_preferente else '—'}</td></tr>
          <tr><td style="padding:8px 0;color:#64748b;font-size:14px;">Ahorro estimado</td>
              <td style="padding:8px 0;font-weight:600;color:#1D9E75;font-size:14px;">{ahorro_txt}</td></tr>
          <tr><td style="padding:8px 0;color:#64748b;font-size:14px;">Origen</td>
              <td style="padding:8px 0;font-size:14px;">{lead.utm_source or 'Directo'} / {lead.utm_medium or '—'}</td></tr>
          <tr><td style="padding:8px 0;color:#64748b;font-size:14px;">Hora</td>
              <td style="padding:8px 0;font-size:14px;">{lead.creado.strftime('%d/%m/%Y %H:%M')}</td></tr>
        </table>
        <div style="margin-top:20px;">
          <a href="https://wa.me/569{lead.telefono}?text=Hola+{lead.nombre.replace(' ', '+')}%2C+soy+asesor+de+AsesoríasIsapres.com+y+quiero+ayudarte+a+encontrar+el+mejor+plan."
             style="background:#25D366;color:white;padding:12px 24px;border-radius:8px;
                    text-decoration:none;font-weight:600;display:inline-block;">
            &#128172; Contactar por WhatsApp
          </a>
        </div>
      </div>
    </div>
    """

    payload = {
        "from": "leads@asesoriasisapres.com",
        "to": [os.environ.get('ASESOR_EMAIL', 'contacto@asesoriasisapres.com')],
        "subject": f"Nuevo lead: {lead.nombre} — {lead.get_situacion_display()}",
        "html": html,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=5)
        r.raise_for_status()
    except Exception as e:
        logger.error(f"Error enviando email para lead #{lead.id}: {e}")
