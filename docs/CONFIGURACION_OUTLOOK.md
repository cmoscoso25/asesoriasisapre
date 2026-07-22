# Configuración de Integración Outlook Calendar

Guía para conectar el módulo `/gestion/` con Microsoft Outlook Calendar.

## Requisitos

- Cuenta Microsoft 365 (o cuenta personal de Outlook)
- Acceso a [Azure Portal](https://portal.azure.com)
- Variables de entorno configuradas en Render.com

---

## Paso 1: Registrar la aplicación en Azure

1. Ve a [portal.azure.com](https://portal.azure.com) e inicia sesión.
2. Busca **"App registrations"** y haz clic en **New registration**.
3. Completa el formulario:
   - **Name**: `AsesoríasIsapres CRM`
   - **Supported account types**: `Accounts in any organizational directory and personal Microsoft accounts`
   - **Redirect URI**: Selecciona `Web` y escribe:
     ```
     https://asesoriasisapres.com/gestion/outlook/callback/
     ```
4. Haz clic en **Register**.

---

## Paso 2: Obtener las credenciales

### Application (client) ID

En la página de la app registrada, copia el valor de **Application (client) ID**. Este es tu `MICROSOFT_CLIENT_ID`.

### Tenant ID

En la misma página, copia el valor de **Directory (tenant) ID**. O usa `common` para permitir cualquier cuenta Microsoft.

### Client Secret

1. En el menú lateral, ve a **Certificates & secrets**.
2. Haz clic en **New client secret**.
3. Pon una descripción (ej: "Render production") y selecciona la expiración (recomendado: 24 meses).
4. Haz clic en **Add**.
5. **Copia el valor inmediatamente** — no lo podrás ver después.

---

## Paso 3: Configurar permisos de la API

1. Ve a **API permissions** → **Add a permission** → **Microsoft Graph**.
2. Selecciona **Delegated permissions** y agrega:
   - `Calendars.ReadWrite`
   - `User.Read`
   - `offline_access` (normalmente ya está incluido)
3. Haz clic en **Add permissions**.
4. **Opcional**: Si usas una cuenta de organización, haz clic en **Grant admin consent**.

---

## Paso 4: Configurar variables en Render.com

En el panel de Render.com, ve a **Environment → Environment Variables** y agrega:

| Variable | Valor |
|---|---|
| `MICROSOFT_CLIENT_ID` | El Application ID que copiaste |
| `MICROSOFT_CLIENT_SECRET` | El Client Secret que copiaste |
| `MICROSOFT_TENANT_ID` | El Tenant ID o `common` |
| `MICROSOFT_REDIRECT_URI` | `https://asesoriasisapres.com/gestion/outlook/callback/` |

Guarda y espera que Render redeploy el servicio.

---

## Paso 5: Conectar la cuenta en el CRM

1. Inicia sesión en `/gestion/` con tu usuario staff.
2. Ve a **Outlook** en el menú lateral.
3. Haz clic en **Conectar con Microsoft**.
4. Autoriza los permisos solicitados.
5. Serás redirigido de vuelta al panel con confirmación de conexión.

---

## Cómo funciona la sincronización

| Acción en CRM | Acción en Outlook |
|---|---|
| Nueva reunión → Guardar | Se crea evento en Outlook Calendar |
| Editar reunión → Guardar | Se actualiza el evento en Outlook |
| Cancelar reunión | El evento queda en Outlook (cancelarlo manualmente si deseas) |

- Los recordatorios (15 min, 30 min, etc.) se sincronizan con Outlook.
- La zona horaria usada es `America/Santiago`.
- Si el token de Outlook expira, se renueva automáticamente con el refresh token.
- Si el refresh token expira (sin uso por 90+ días), debes reconectar desde `/gestion/outlook/`.

---

## Renovación del Client Secret

Los client secrets expiran (1 o 2 años). Cuando expire:

1. Ve a Azure Portal → tu app → **Certificates & secrets**.
2. Crea un nuevo secret.
3. Actualiza `MICROSOFT_CLIENT_SECRET` en las variables de entorno de Render.
4. Desconecta y vuelve a conectar Outlook desde `/gestion/outlook/`.

---

## Solución de problemas

**Error: "MICROSOFT_CLIENT_ID y MICROSOFT_CLIENT_SECRET son requeridos"**
→ Las variables de entorno no están configuradas en Render.

**Error: "Sesión OAuth expirada"**
→ El proceso de conexión tardó más de la sesión. Intenta de nuevo.

**Error: "AADSTS70011: The provided value for the input parameter 'scope' is not valid"**
→ Los permisos de la app en Azure no incluyen `Calendars.ReadWrite`. Agrégalos en API permissions.

**Las reuniones no aparecen en Outlook**
→ Verifica en `/gestion/outlook/` que la cuenta esté conectada. Si aparece "desconectada", reconecta.
