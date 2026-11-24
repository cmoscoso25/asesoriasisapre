from django.core.management.base import BaseCommand

from gestion.db_security import asegurar_rls


class Command(BaseCommand):
    help = ('Activa Row Level Security en las tablas de public que no lo tengan y '
            'revoca acceso de los roles anon/authenticated de Supabase. Idempotente.')

    def add_arguments(self, parser):
        parser.add_argument('--database', default='default')

    def handle(self, *args, **options):
        corregidas = asegurar_rls(using=options['database'])
        if corregidas:
            self.stdout.write(f"RLS activado en: {', '.join(corregidas)}")
        else:
            self.stdout.write('Sin tablas pendientes (o base de datos no PostgreSQL).')
