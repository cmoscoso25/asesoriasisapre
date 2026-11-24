"""
Sincronización Lead (formulario web) → Prospecto (CRM).

Reglas:
- Si la persona NO existe en el CRM → se crea su ficha.
- Si YA existe (mismo celular o mismo email) → no se duplica: se agrega una
  nota automática a su ficha, la prioridad sube a Alta, el próximo
  seguimiento queda para hoy y, si estaba archivada o cerrada sin éxito,
  se reactiva. Así un contacto que vuelve a escribir nunca pasa inadvertido.
- Los teléfonos se comparan por sus últimos 9 dígitos, sin importar el
  formato (982479504, +56982479504 y +56 9 8247 9504 son el mismo número).
"""
import logging

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger('gestion')

CREADO = 'creado'
EXISTENTE = 'existente'
OMITIDO = 'omitido'

ESTADOS_CERRADOS = ('no_concretado', 'sin_respuesta')


def normalizar_telefono(valor):
    """Últimos 9 dígitos del número (celular chileno sin prefijo 56)."""
    digitos = ''.join(ch for ch in str(valor or '') if ch.isdigit())
    return digitos[-9:] if len(digitos) >= 9 else digitos


def buscar_prospecto(telefono='', email='', excluir_pk=None):
    """Busca un prospecto (activo o archivado) por celular o email."""
    from gestion.models import Prospecto

    tel = normalizar_telefono(telefono)
    if len(tel) == 9:
        # Prefiltro en BD por los últimos 4 dígitos; comparación exacta en Python
        candidatos = Prospecto.objects.filter(telefono__contains=tel[-4:])
        if excluir_pk:
            candidatos = candidatos.exclude(pk=excluir_pk)
        for p in candidatos.order_by('-activo', '-creado'):
            if normalizar_telefono(p.telefono) == tel:
                return p

    email = (email or '').strip()
    if email:
        qs = Prospecto.objects.filter(email__iexact=email)
        if excluir_pk:
            qs = qs.exclude(pk=excluir_pk)
        return qs.order_by('-activo', '-creado').first()
    return None


def origen_desde_utm(utm_source):
    s = (utm_source or '').strip().lower()
    if s in ('ig', 'instagram'):
        return 'instagram'
    if s in ('fb', 'facebook', 'meta'):
        return 'facebook'
    return 'web'


def _resumen_lead(lead):
    partes = [
        lead.get_situacion_display() if lead.situacion else '',
        lead.get_prevision_actual_display() if lead.prevision_actual else '',
        lead.get_clinica_preferente_display() if lead.clinica_preferente else '',
    ]
    origen = '/'.join(x for x in (lead.utm_source, lead.utm_medium, lead.utm_campaign) if x) or 'directo'
    detalle = ', '.join(p for p in partes if p) or 'sin diagnóstico'
    return f"{detalle}. Origen: {origen}."


def _datos_nuevo_prospecto(lead):
    return dict(
        lead=lead,
        nombre=lead.nombre,
        rut=lead.rut,
        telefono=lead.telefono,
        email=lead.email,
        region=lead.region,
        isapre_actual=lead.prevision_actual,
        motivo_asesoria=dict(lead.SITUACION_CHOICES).get(lead.situacion, ''),
        renta=lead.renta,
        edad=lead.edad,
        cargas=lead.cargas,
        clinica_preferente=lead.clinica_preferente,
        origen=origen_desde_utm(lead.utm_source),
        estado='nuevo',
        prioridad='media',
    )


@transaction.atomic
def sincronizar_lead(lead, registrar_repeticion=True):
    """
    Vincula un Lead con el CRM. Devuelve (prospecto, resultado) con
    resultado en {CREADO, EXISTENTE, OMITIDO}.

    registrar_repeticion=False (recuperación retroactiva): si la persona ya
    existe no se toca su ficha (evita llenar de notas antiguas o subir
    prioridades por leads viejos); solo se vincula el lead si la ficha no
    tenía uno.
    """
    from gestion.models import GestionProspecto, Prospecto

    if Prospecto.objects.filter(lead=lead).exists():
        return Prospecto.objects.get(lead=lead), OMITIDO

    existente = buscar_prospecto(lead.telefono, lead.email)

    if existente is None:
        prospecto = Prospecto.objects.create(**_datos_nuevo_prospecto(lead))
        logger.info("Prospecto %s creado desde Lead %s", prospecto.pk, lead.pk)
        return prospecto, CREADO

    campos = []
    if existente.lead_id is None:
        existente.lead = lead
        campos.append('lead')

    if not registrar_repeticion:
        if campos:
            existente.save(update_fields=campos + ['actualizado'])
        return existente, EXISTENTE

    cambios = []
    if not existente.activo:
        existente.activo = True
        campos.append('activo')
        cambios.append('ficha reactivada (estaba archivada)')
    if existente.estado in ESTADOS_CERRADOS:
        cambios.append(f'estado "{existente.get_estado_display()}" → "Nuevo contacto"')
        existente.estado = 'nuevo'
        campos.append('estado')
    if existente.prioridad != 'alta':
        existente.prioridad = 'alta'
        campos.append('prioridad')
    hoy = timezone.localdate()
    if existente.proximo_seguimiento != hoy:
        existente.proximo_seguimiento = hoy
        campos.append('proximo_seguimiento')
    if campos:
        existente.save(update_fields=campos + ['actualizado'])

    descripcion = f"Nuevo formulario web recibido (Lead #{lead.pk}): {_resumen_lead(lead)}"
    if cambios:
        descripcion += ' ' + '; '.join(cambios).capitalize() + '.'
    GestionProspecto.objects.create(
        prospecto=existente,
        usuario=None,
        tipo='nota',
        descripcion=descripcion,
        proxima_accion='Contactar: volvió a llenar el formulario',
        fecha_proxima_accion=hoy,
    )
    logger.info("Lead %s repetido: nota agregada al prospecto %s", lead.pk, existente.pk)
    return existente, EXISTENTE
