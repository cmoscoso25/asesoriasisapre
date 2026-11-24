import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger('gestion')


@receiver(post_save, sender='leads.Lead')
def crear_prospecto_desde_lead(sender, instance, created, **kwargs):
    """
    Lead nuevo del formulario web → ficha en el CRM (o nota en la ficha
    existente si la persona ya estaba). El resultado queda en atributos
    temporales del lead para que el email al asesor lo informe:
      instance._crm_resultado: 'creado' | 'existente' | 'error'
      instance._crm_prospecto: Prospecto o None
    """
    if not created:
        return

    from gestion.services.leads_crm import sincronizar_lead

    try:
        prospecto, resultado = sincronizar_lead(instance)
        instance._crm_resultado = resultado
        instance._crm_prospecto = prospecto
    except Exception:
        instance._crm_resultado = 'error'
        instance._crm_prospecto = None
        logger.exception("Error sincronizando Lead %s con el CRM", instance.pk)
