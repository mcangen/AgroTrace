# Desplegar AgroTrace en Render

Guía paso a paso para el primer despliegue. El `render.yaml` de la raíz del
repo ya describe todo lo que hay que crear (un servicio web + una base
Postgres); esta guía es solo la parte que Render no puede automatizar: las
cuentas y las claves.

## 0. Antes de empezar

- El código vive en la rama **`produccion-python-react`** (no en `master`
  todavía). Al conectar el repo en Render, elige esa rama.
- Vas a necesitar, en este orden: una cuenta de Cloudflare (para las fotos),
  opcionalmente una API key de Gemini y credenciales SMTP, y una cuenta de
  Render.

## 1. Cloudflare R2 (almacenamiento de fotos)

Sin esto la app funciona igual, pero cualquier foto que alguien suba se
perderá en el próximo despliegue (Render no conserva el disco entre
despliegues en el plan gratuito).

1. Crea una cuenta en [dash.cloudflare.com](https://dash.cloudflare.com) si no
   tienes una (es gratis).
2. En el menú lateral, entra a **R2 Object Storage** → **Create bucket**.
   Nómbralo `agrotrace-photos` (o el nombre que quieras).
3. Abre el bucket → **Settings** → **Public access** → activa **Allow public
   access** con el subdominio `r2.dev` que te ofrece. Copia esa URL completa
   (algo como `https://pub-xxxxxxxx.r2.dev`) — es tu
   `AGROTRACE_S3_PUBLIC_BASE_URL`.
4. Ve a **R2** → **Manage API tokens** → **Create API token**. Permisos:
   "Object Read & Write", alcance: solo ese bucket. Al crearlo te muestra
   **una sola vez**:
   - `Access Key ID` → `AGROTRACE_S3_ACCESS_KEY_ID`
   - `Secret Access Key` → `AGROTRACE_S3_SECRET_ACCESS_KEY`
   - El panel también te muestra tu **Account ID** (o lo ves en la URL del
     dashboard). Con eso arma:
     `AGROTRACE_S3_ENDPOINT_URL = https://<ACCOUNT_ID>.r2.cloudflarestorage.com`

Guarda estos 4 valores en un lugar seguro — los vas a pegar en Render en el
paso 3. `AGROTRACE_S3_BUCKET` es el nombre que le pusiste al bucket
(`agrotrace-photos`), y `AGROTRACE_S3_REGION` déjalo en `auto`.

> **Verifica al crear la cuenta**: los límites de la capa gratuita de R2
> (hoy, cuando se escribió esto: 10 GB de almacenamiento y sin costo de
> egreso) pueden haber cambiado — revísalos en la página de precios de
> Cloudflare R2 antes de asumir que sigue siendo gratis a cualquier escala.

## 2. Gemini y correo (opcionales, pero recomendados)

- **Gemini**: consigue una key en
  [aistudio.google.com/apikey](https://aistudio.google.com/apikey). Sin ella,
  los agentes de IA funcionan con contenido de respaldo (la app no se rompe,
  pero pierde su función más vistosa).
- **Correo** (notificaciones de mensajes, recuperar contraseña): cualquier
  SMTP sirve. Con Gmail: host `smtp.gmail.com`, puerto `587`, usuario tu
  correo, contraseña una ["contraseña de aplicación"](https://myaccount.google.com/apppasswords)
  (no la contraseña normal de la cuenta). Sin esto configurado, los correos
  quedan en el log del servicio en vez de enviarse — otra vez, no rompe nada.

## 3. Desplegar en Render

1. Crea una cuenta en [render.com](https://render.com) (puedes entrar con tu
   cuenta de GitHub directamente).
2. **New +** → **Blueprint**.
3. Conecta tu cuenta de GitHub si es la primera vez, y selecciona el
   repositorio `mcangen/AgroTrace`.
4. Render detecta `render.yaml` en la raíz. **Importante**: en el selector de
   rama, cambia de `master` a **`produccion-python-react`**.
5. Render te muestra un resumen: un servicio web `agrotrace` + una base
   `agrotrace-db`, ambos en el plan gratuito. Antes de confirmar, te va a
   pedir valores para cada variable marcada `sync: false` en el blueprint:
   pega ahí los 4 valores de R2 del paso 1, tu `GEMINI_API_KEY` si la tienes,
   y las 4 variables de SMTP si las tienes. Las que no tengas, déjalas vacías
   por ahora — la app las trata como "no configurado" y sigue funcionando.
6. **Apply** / **Create**. El primer despliegue tarda varios minutos: instala
   dependencias de Python, instala dependencias de Node, construye el
   frontend, y arranca el backend.

## 4. Después del primer despliegue

1. Render te asigna una URL — algo como `https://agrotrace.onrender.com` (si
   ese nombre ya estaba tomado, será distinto). **Cópiala.**
2. Si la URL real es distinta a `https://agrotrace.onrender.com`: en el
   dashboard del servicio → **Environment**, edita
   `AGROTRACE_PUBLIC_WEB_URL` y `AGROTRACE_CORS_ORIGINS` para que coincidan
   con la URL real, y guarda (esto redespliega automáticamente). Sin este
   paso, los enlaces de los QR y de los correos de recuperación de
   contraseña apuntarían a la URL equivocada.
3. Abre esa URL. Deberías ver la landing de AgroTrace. Crea una cuenta desde
   ahí y prueba el flujo completo: crear finca → registrar lote → sellar un
   evento → ver el pasaporte público.
4. Revisa los **Logs** del servicio en Render (pestaña "Logs") al arrancar:
   debe decir `IA activa: ...` si puso la key de Gemini, o `IA en modo
   respaldo` si no. Igual para el correo: si mandas un mensaje desde un
   pasaporte público y no configuraste SMTP, el correo completo aparece en
   los logs en vez de llegar a una bandeja real — útil para confirmar que el
   contenido es correcto antes de configurar SMTP de verdad.

## Limitaciones conocidas de este primer despliegue

- **El servicio gratuito de Render se "duerme"** tras un rato sin tráfico; la
  primera visita después de eso tarda ~30 segundos en responder mientras
  arranca. Pasar al plan de pago (~$7/mes) lo mantiene siempre activo.
- **Sin migraciones de esquema** (no hay Alembic): las tablas se crean solas
  la primera vez (`Base.metadata.create_all`), pero un cambio de esquema
  futuro sobre datos ya existentes en producción necesitará una migración
  escrita a mano o agregar Alembic — no está cubierto todavía.
- **No se probó contra un Postgres real antes de este despliegue** (no había
  Docker ni Postgres instalado en la máquina de desarrollo): el código se
  revisó con cuidado para ser compatible, pero el primer despliegue real en
  Render *es* la primera prueba de verdad contra Postgres. Si algo falla en
  el arranque, copia el error de los Logs y lo resolvemos.
- **La cuenta demo viene desactivada** en producción
  (`AGROTRACE_SEED_DEMO=false`) a propósito — no tiene sentido que un login
  público de prueba conviva con cuentas reales.
- **El código sigue en la rama `produccion-python-react`**, no en `master`.
  Cuando confirmes que todo funciona bien en producción, hacer `master` el
  reflejo de esa rama (merge o fast-forward) es una decisión tuya — no lo
  hice automáticamente.
