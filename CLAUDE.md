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
- IP del cliente: siempre `core.security.get_client_ip` (usa `CF-Connecting-IP` de Cloudflare; `X-Forwarded-For` es falsificable). También la usa django-axes (`AXES_CLIENT_IP_CALLABLE`)
- `DEBUG` es `False` por defecto en Render (variable `RENDER`); `True` solo en local
- `asesoriasisapre.onrender.com` redirige 301 a `asesoriasisapres.com` (`core.security.SecurityHeadersMiddleware`, que además envía `Permissions-Policy`)
- El email de nuevo lead NO incluye RUT ni renta: solo enlace a la ficha del CRM
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
| `ULTRAMSG_INSTANCE` | ID de instancia UltraMsg, ej: `instance123456` |
| `ULTRAMSG_TOKEN` | Token de la instancia UltraMsg |
| `ULTRAMSG_PHONE` | Número destino WhatsApp, ej: `+56912345678` |
| `CRON_SECRET` | Token secreto para proteger `/gestion/cron/recordatorios/` |
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
- Tests: `py manage.py test leads gestion` — 65 tests, todos deben pasar
- Todas las vistas con `@staff_required` son `never_cache` (datos personales)
- Cron: `/gestion/cron/recordatorios/` autentica con cabecera `X-Cron-Secret` (el `?secret=` en URL es legado y registra un warning)

## Meta Pixel

- ID `3609526355889947` (default de `META_PIXEL_ID`; vacío en Render = desactivado). Solo se carga con `DEBUG=False`.
- Código en `static/js/meta-pixel.js` (sin script inline por la CSP), incluido una vez en `templates/base.html`. `autoConfig` desactivado.
- Eventos: `PageView` (todas las páginas públicas), `Contact` (clic en enlaces `wa.me`), `Lead` en `/gracias/` vía marca de sesión de un solo uso `meta_lead_event` (se crea en `leads.views.nuevo_lead`, se consume en `core.views.gracias`, que es `@never_cache`).
- **Nunca** enviar a Meta datos del formulario/diagnóstico (RUT, renta, clínica, situación) ni parámetros personalizados.

## Integración Lead → Prospecto

Signal en `gestion/signals.py`: cuando se crea un `Lead` desde el formulario web, se crea automáticamente un `Prospecto` en el CRM. Dedup por teléfono y email.

## Supabase / RLS

- RLS activado (`ENABLE`) en todas las tablas públicas
- **No usar** `FORCE ROW LEVEL SECURITY` — bloquea al usuario `postgres` (Django) y tira la app
- Django se conecta directo con el usuario `postgres` (no usa Supabase REST API)
- **Automático:** tras cada `migrate` (señal `post_migrate` en `gestion/apps.py`) y en `build.sh` (`py manage.py asegurar_rls`) se activa RLS en tablas nuevas de `public` y se revoca todo a `anon`/`authenticated`. Lógica en `gestion/db_security.py`. Las migraciones que crean tablas ya no dejan tablas expuestas.
