from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from gestion.models import Reunion
from gestion.notifications import enviar_email_recordatorio, enviar_whatsapp_recordatorio


class Command(BaseCommand):
    help = 'Envía recordatorios (email + WhatsApp) 15 min antes de cada reunión agendada'

    def handle(self, *args, **options):
        now = timezone.localtime(timezone.now())
        # Ventana: reuniones que empiezan entre 10 y 20 minutos desde ahora
        win_start = now + timedelta(minutes=10)
        win_end   = now + timedelta(minutes=20)

        if win_start.date() == win_end.date():
            reuniones = Reunion.objects.filter(
                fecha=win_start.date(),
                hora_inicio__gte=win_start.time(),
                hora_inicio__lte=win_end.time(),
                estado__in=['agendada', 'confirmada'],
                recordatorio_enviado=False,
            ).select_related('prospecto')
        else:
            # La ventana cruza medianoche (caso raro)
            reuniones = (
                Reunion.objects.filter(
                    fecha=win_start.date(),
                    hora_inicio__gte=win_start.time(),
                    estado__in=['agendada', 'confirmada'],
                    recordatorio_enviado=False,
                ) | Reunion.objects.filter(
                    fecha=win_end.date(),
                    hora_inicio__lte=win_end.time(),
                    estado__in=['agendada', 'confirmada'],
                    recordatorio_enviado=False,
                )
            ).select_related('prospecto')

        total = reuniones.count()
        if total == 0:
            self.stdout.write('Sin recordatorios pendientes.')
            return

        enviados = 0
        for reunion in reuniones:
            email_ok = enviar_email_recordatorio(reunion)
            wa_ok    = enviar_whatsapp_recordatorio(reunion)
            if email_ok or wa_ok:
                reunion.recordatorio_enviado = True
                reunion.save(update_fields=['recordatorio_enviado'])
                enviados += 1
                self.stdout.write(f"  Reunión #{reunion.pk} '{reunion.titulo}' — notificado OK")
            else:
                self.stderr.write(f"  Reunión #{reunion.pk} '{reunion.titulo}' — falló el envío")

        self.stdout.write(
            self.style.SUCCESS(f"Recordatorios: {enviados}/{total} enviados.")
        )
