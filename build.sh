#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py createcachetable django_cache_ratelimit || true
# Seguridad Supabase: RLS en todas las tablas de public + sin acceso para anon/authenticated
python manage.py asegurar_rls

# Crear superusuario si las variables están definidas
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py createsuperuser --no-input || true
fi
