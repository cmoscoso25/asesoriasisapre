import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger('gestion')


@receiver(post_save, sender='leads.Lead')
def crear_prospecto_desde_lead(sender, instance, created, **kwargs):
    if not created:
        return

    from gestion.models import Prospecto

    # Dedup: si ya existe un prospecto con el mismo teléfono, no crear otro
    if Prospecto.objects.filter(telefono=instance.telefono).exists():
        logger.debug("Lead %s ya tiene prospecto por teléfono, omitiendo.", instance.pk)
        return

    # Dedup por email (solo si email no está vacío)
    if instance.email and Prospecto.objects.filter(email=instance.email).exists():
        logger.debug("Lead %s ya tiene prospecto por email, omitiendo.", instance.pk)
        return

    try:
        Prospecto.objects.create(
            lead=instance,
            nombre=instance.nombre,
            rut=instance.rut,
            telefono=instance.telefono,
            email=instance.email,
            region=instance.region,
            isapre_actual=instance.prevision_actual,
            motivo_asesoria=dict(instance.SITUACION_CHOICES).get(instance.situacion, ''),
            renta=instance.renta,
            edad=instance.edad,
            cargas=instance.cargas,
            clinica_preferente=instance.clinica_preferente,
            origen='web',
            estado='nuevo',
            prioridad='media',
        )
        logger.info("Prospecto creado automáticamente desde Lead %s (%s)", instance.pk, instance.nombre)
    except Exception as exc:
        logger.error("Error creando prospecto desde Lead %s: %s", instance.pk, exc)
