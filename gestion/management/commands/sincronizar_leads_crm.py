from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from gestion.services.leads_crm import CREADO, EXISTENTE, buscar_prospecto, sincronizar_lead
from leads.models import Lead


class Command(BaseCommand):
    help = ('Crea en el CRM las fichas faltantes de leads que no tienen prospecto. '
            'No duplica personas que ya existen (mismo celular o email) ni modifica sus fichas. '
            'Usa --dry-run para ver qué haría sin guardar nada.')

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Solo mostrar, sin guardar cambios.')
        parser.add_argument('--desde', help='Solo leads creados desde esta fecha (AAAA-MM-DD).')

    def handle(self, *args, **opts):
        qs = Lead.objects.filter(prospecto__isnull=True).order_by('creado')
        if opts['desde']:
            try:
                desde = datetime.strptime(opts['desde'], '%Y-%m-%d')
            except ValueError:
                raise CommandError('--desde debe tener formato AAAA-MM-DD')
            qs = qs.filter(creado__gte=timezone.make_aware(desde))

        creados = existentes = 0
        vistos = {}  # en dry-run, agrupa leads de la misma persona
        for lead in qs:
            if opts['dry_run']:
                clave = (lead.telefono[-9:], (lead.email or '').lower())
                if buscar_prospecto(lead.telefono, lead.email) or clave in vistos:
                    existentes += 1
                    accion = 'ya existe en el CRM → sin cambios'
                else:
                    vistos[clave] = True
                    creados += 1
                    accion = 'SE CREARÍA ficha'
            else:
                _, resultado = sincronizar_lead(lead, registrar_repeticion=False)
                if resultado == CREADO:
                    creados += 1
                    accion = 'ficha creada'
                else:
                    existentes += 1
                    accion = 'ya existía en el CRM → sin cambios' if resultado == EXISTENTE else 'omitido'
            self.stdout.write(f"Lead #{lead.pk} {lead.nombre} ({lead.creado:%d/%m/%Y}): {accion}")

        modo = ' (simulación, nada guardado)' if opts['dry_run'] else ''
        self.stdout.write(self.style.SUCCESS(
            f"Fichas {'a crear' if opts['dry_run'] else 'creadas'}: {creados} · "
            f"Personas ya existentes: {existentes}{modo}"
        ))
