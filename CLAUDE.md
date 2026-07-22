# CLAUDE.md — AsesoríasIsapres

Instrucciones para Claude Code al trabajar en este proyecto.

## Proyecto

Sitio web Django para asesoría de isapres en Chile. Deploy automático: GitHub `main` → Render.com (Starter plan, ~$7/mes). Base de datos: Supabase PostgreSQL (Session Pooler, IPv4).

## Apps

- **`core`** — landing pages, SEO, sitemap, redirects 301
- **`leads`** — captura de formulario público, validación RUT/teléfono, notificaciones email
- **`gestion`** — módulo CRM privado (`/gestion/`), solo staff

## Reglas de seguridad (NUNCA violar)

- `SECRET_KEY` siempre desde env var; jamás hardcodeada
- `.env` nunca en Git (está en `.gitignore`)
- Admin en `/gestion-interna/` (no `/admin/`)
- Credenciales DB solo desde variables de entorno
- `SECURE_*` y cookies seguras se activan solo cuando `DEBUG=False`
- Rate limit leads: máx 3 envíos/IP/10 min vía `DatabaseCache`
- Tokens Microsoft OAuth en campo de DB — no en logs

## Variables de entorno (Render)

| Variable | Descripción |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `False` en producción |
| `ALLOWED_HOSTS` | `asesoriasisapres.com,www.asesoriasisapres.com,asesoriasisapre.onrender.com` |
| `DB_NAME/USER/PASSWORD/HOST/PORT` | Supabase PostgreSQL Session Pooler |
| `DB_ENGINE` | `postgresql` |
| `RESEND_API_KEY` | API key de Resend para emails |
| `ASESOR_EMAILS` | Email(s) del asesor separados por coma |
| `RESEND_FROM_EMAIL` | Email remitente (verificado en Resend) |
| `TAWKTO_ID` | ID del widget de Tawk.to |
| `MICROSOFT_CLIENT_ID` | Azure App Registration Client ID (opcional) |
| `MICROSOFT_CLIENT_SECRET` | Azure App Registration Secret (opcional) |
| `MICROSOFT_TENANT_ID` | `common` o ID del tenant (opcional) |
| `MICROSOFT_REDIRECT_URI` | `https://asesoriasisapres.com/gestion/outlook/callback/` (opcional) |
| `DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD` | Para crear superusuario en build |

## CSS (variables existentes en main.css)

```
--azul-profundo: #042C53
--azul-primario: #0C447C
--azul-medio:    #185FA5
--verde-cta:     #1D9E75
--verde-oscuro:  #0F6E56
--gris-texto:    #64748B
--gris-fondo:    #F7F8FA
```

CSS del módulo gestion: `static/css/gestion.css` (prefijo `.g-`).

## CSP (Content Security Policy)

Solo `'self'` + Tawk.to. **Sin CDN externos**. Todo JS/CSS debe estar en `static/`. No usar `unsafe-inline` para scripts.

## Comandos frecuentes

```bash
py manage.py makemigrations gestion
py manage.py migrate
py manage.py test gestion
py manage.py collectstatic --no-input
```

## Módulo /gestion/ (CRM)

- URL base: `/gestion/`
- Solo usuarios con `is_staff=True` (decorador `@staff_required` en `gestion/views.py`)
- Login redirige a `/gestion-interna/login/`
- Sincronización Outlook: opcional, requiere `MICROSOFT_CLIENT_ID` configurado
- Tests: `py manage.py test gestion` — 35 tests, todos deben pasar

## Integración Lead → Prospecto

Signal en `gestion/signals.py`: cuando se crea un `Lead` desde el formulario web, se crea automáticamente un `Prospecto` en el CRM. Dedup por teléfono y email.

## Supabase / RLS

- RLS activado (`ENABLE`) en todas las tablas públicas
- **No usar** `FORCE ROW LEVEL SECURITY` — bloquea al usuario `postgres` (Django) y tira la app
- Django se conecta directo con el usuario `postgres` (no usa Supabase REST API)
