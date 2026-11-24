from django.apps import AppConfig


class GestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion'
    verbose_name = 'Gestión Comercial'

    def ready(self):
        import gestion.signals  # noqa
        from django.db.models.signals import post_migrate
        from gestion.db_security import post_migrate_handler

        # Se ejecuta una vez por `migrate` (sender=esta app): activa RLS en
        # tablas nuevas de public y revoca acceso de anon/authenticated.
        post_migrate.connect(post_migrate_handler, sender=self,
                             dispatch_uid='gestion_asegurar_rls')
