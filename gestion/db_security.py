"""
Endurecimiento de seguridad de la base de datos en Supabase.

Tras cada `migrate` (build.sh lo ejecuta en cada deploy de Render):
  1. Activa Row Level Security (ENABLE, nunca FORCE) en toda tabla del schema
     public que no lo tenga. Django se conecta como dueño de las tablas
     (`postgres`), por lo que ENABLE no le afecta; FORCE sí lo bloquearía.
  2. Revoca a los roles de la API pública de Supabase (anon, authenticated)
     todo privilegio sobre tablas, secuencias y funciones de public, también
     para objetos que se creen en el futuro.

Es idempotente y solo actúa en PostgreSQL. Los pasos de REVOKE se omiten si los
roles de Supabase no existen (p. ej. un PostgreSQL local).
"""
import logging

from django.db import connections, transaction

logger = logging.getLogger('gestion')

API_ROLES = ('anon', 'authenticated')

TABLAS_SIN_RLS_SQL = """
    SELECT c.relname
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relkind IN ('r', 'p')
      AND NOT c.relrowsecurity
    ORDER BY c.relname
"""


def _ejecutar(cursor, sql, params=None):
    """Ejecuta una sentencia en un savepoint para que un fallo no aborte el resto."""
    try:
        with transaction.atomic(using=cursor.db.alias):
            cursor.execute(sql, params)
        return True
    except Exception as exc:  # permisos insuficientes, objeto inexistente, etc.
        logger.warning("db_security: no se pudo ejecutar %r: %s", sql.strip()[:120], exc)
        return False


def asegurar_rls(using='default'):
    """Activa RLS y revoca acceso de la API pública. Devuelve las tablas corregidas."""
    connection = connections[using]
    if connection.vendor != 'postgresql':
        return []

    corregidas = []
    with connection.cursor() as cursor:
        cursor.execute(TABLAS_SIN_RLS_SQL)
        tablas = [row[0] for row in cursor.fetchall()]
        for tabla in tablas:
            sql = f'ALTER TABLE public.{connection.ops.quote_name(tabla)} ENABLE ROW LEVEL SECURITY'
            if _ejecutar(cursor, sql):
                corregidas.append(tabla)

        cursor.execute(
            "SELECT rolname FROM pg_roles WHERE rolname = ANY(%s)", [list(API_ROLES)]
        )
        roles = [row[0] for row in cursor.fetchall()]
        if roles:
            destinatarios = ', '.join(connection.ops.quote_name(r) for r in roles)
            for objeto in ('TABLES', 'SEQUENCES', 'FUNCTIONS'):
                _ejecutar(cursor, f'REVOKE ALL ON ALL {objeto} IN SCHEMA public FROM {destinatarios}')
                _ejecutar(
                    cursor,
                    f'ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON {objeto} FROM {destinatarios}',
                )

    if corregidas:
        logger.warning("db_security: RLS activado en %d tabla(s): %s", len(corregidas), ', '.join(corregidas))
    return corregidas


def post_migrate_handler(sender, using='default', **kwargs):
    asegurar_rls(using=using)
