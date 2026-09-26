# AgroTrace

Trazabilidad agrícola verificable para pequeños productores, con cadena de hashes
SHA-256 y agentes de IA sobre **Gemini**.

Cada hecho del campo (siembra, fertilización, cosecha, secado, empaque…) se sella
en una cadena criptográfica donde el hash de cada evento depende del anterior.
Alterar un evento pasado invalida todos los siguientes, y cualquiera puede
comprobarlo desde el pasaporte público del lote.

---

## Estructura

```
AgroTrace/
├── backend/          API en Python · FastAPI + SQLAlchemy + Gemini
│   └── app/
│       ├── ai/       agentes, cliente de Gemini, esquemas de salida y respaldos
│       ├── api/      routers REST y dependencias de autenticación
│       ├── core/     configuración y seguridad (JWT, bcrypt)
│       ├── db/       sesión, metadatos y datos de demostración
│       ├── models/   entidades SQLAlchemy
│       ├── schemas/  contratos Pydantic de entrada y salida
│       └── services/ cadena de hashes, trazabilidad y QR
├── frontend/         SPA en TypeScript · React 19 + Vite + TanStack Query
│   └── src/
│       ├── components/  shell, gráficas, línea de tiempo de la cadena, panel de IA
│       ├── lib/         cliente HTTP tipado, sesión, formato
│       ├── pages/       landing, auth, panel, lotes, fincas, asistente, pasaporte
│       └── styles/      tokens de diseño y hojas base
└── legacy/           proyecto original de la hackatón (Spring Boot + HTML)
```

El backend original en Java se conservó en `legacy/` como referencia. No se usa.

---

## Puesta en marcha

Necesitas **Python 3.11+** y **Node 20+**.

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
copy .env.example .env          # cp en macOS / Linux
python -m uvicorn app.main:app --reload --port 8000
```

API en `http://localhost:8000` · documentación interactiva en `/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Aplicación en `http://localhost:5173`. Vite reenvía `/api` al backend, así que no
hay que configurar CORS en desarrollo.

### 3. Entrar

La primera vez que arranca, el backend siembra una cuenta de demostración con dos
fincas, tres lotes y dieciséis eventos ya sellados:

```
demo@agrotrace.co
agrotrace2026
```

También puedes crear una cuenta nueva desde `/crear-cuenta`.

---

## Conectar Gemini

La aplicación **funciona sin API key**: los agentes devuelven contenido de
respaldo y la interfaz lo marca explícitamente como tal. Para activar el modelo:

1. Consigue una key en <https://aistudio.google.com/apikey>.
2. Ponla en `backend/.env` **sin prefijo** (así la nombran el SDK y la documentación
   de Google; la app la resuelve con un `validation_alias` explícito):

   ```env
   GEMINI_API_KEY=tu-key-aqui
   ```

3. Reinicia el backend. El indicador del panel lateral pasa a «IA activa», y
   `GET /api/v1/ai/status` debe responder `"enabled": true`.

### Modelos y resiliencia

```env
AGROTRACE_GEMINI_MODEL=gemini-flash-latest
AGROTRACE_GEMINI_MODEL_PRO=gemini-pro-latest
AGROTRACE_GEMINI_MODEL_FALLBACK=gemini-3.1-flash-lite
AGROTRACE_GEMINI_MAX_RETRIES=3
AGROTRACE_GEMINI_TIMEOUT_SECONDS=20
AGROTRACE_GEMINI_DEADLINE_SECONDS=45
```

Los alias `-latest` evitan que la app se rompa cuando Google retira una versión
concreta. Si prefieres fijar una versión reproducible, usa un nombre exacto y
comprueba `/api/v1/ai/status` después de cambiarlo.

Ante un fallo transitorio (503 por demanda, 429 por cuota) el cliente reintenta
con espera exponencial y, si el modelo principal sigue sin responder, prueba el de
respaldo. Todo ello dentro de un presupuesto total (`DEADLINE_SECONDS`), de modo
que una caída del servicio nunca deja la petición HTTP colgada: se responde con el
contenido de respaldo y la interfaz lo marca.

Para ver qué modelos habilita tu key:

```bash
python -c "from google import genai; from app.core.config import settings; \
[print(m.name) for m in genai.Client(api_key=settings.gemini_api_key).models.list()]"
```

### Migrar a Vertex AI

`google-genai` es el mismo cliente para la Gemini Developer API y para Vertex AI,
así que el cambio no toca código:

```env
AGROTRACE_USE_VERTEX=true
AGROTRACE_GCP_PROJECT=tu-proyecto
AGROTRACE_GCP_LOCATION=us-central1
```

Autentícate con `gcloud auth application-default login` y reinicia. La decisión
se resuelve en [`backend/app/ai/client.py`](backend/app/ai/client.py).

---

## Los agentes

Todos reciben únicamente datos ya sellados en la cadena del lote, construidos por
`build_context()` en [`backend/app/ai/agents.py`](backend/app/ai/agents.py). Si un
dato no está registrado, se le instruye omitirlo en lugar de estimarlo.

| Agente | Qué produce | Salida |
|---|---|---|
| **Narrativa** | Historia de origen ES/EN y notas sensoriales | JSON estructurado |
| **Ficha de exportación** | Ficha técnica bilingüe para importadores | JSON estructurado |
| **Análisis agronómico** | Diagnóstico, puntaje y 3–5 hallazgos accionables | JSON estructurado |
| **Asistente** | Respuestas abiertas sobre la operación | Texto |

Los tres primeros usan **salida estructurada nativa** (`response_schema`), que
garantiza la forma del JSON en lugar de pedirla en el prompt y parsear a mano.

Cada ejecución queda registrada en la tabla `agent_runs` con modelo, latencia y
tokens, y se muestra en el panel. Si el modelo falla, el agente devuelve el
respaldo y marca la ejecución como `FALLBACK` o `ERROR` — nunca tumba la petición.

---

## La cadena de trazabilidad

```
chain_hash(n) = SHA256( payload(n) + "|" + chain_hash(n-1) )
chain_hash(0) = SHA256( payload(0) + "|GENESIS" )
```

`verify_chain()` recalcula la cadena completa y reporta el primer eslabón roto.
El payload se serializa con claves ordenadas, de modo que el hash dependa del
contenido y no del orden en que llegó el JSON.

### Fotos de evidencia

Las fotos se suben **antes** de sellar el evento, y su huella SHA-256 entra al
payload que se firma (`fotos_sha256`). Eso las amarra a la cadena: si alguien
reemplaza el archivo en disco, su huella deja de coincidir con la sellada y tanto
el panel como el pasaporte público marcan esa foto como alterada — sin que la
cadena de eventos en sí se vea afectada, porque el payload no cambió.

Los archivos viven en `backend/uploads/` con su propio hash como nombre (evita
colisiones y travesía de rutas). Una foto ya sellada no se puede borrar.

### Clima

`GET /farms/{id}/clima` usa [Open-Meteo](https://open-meteo.com) — sin API key ni
registro. Las coordenadas se resuelven automáticamente desde el municipio la
primera vez que se consulta, y las alertas (lluvia fuerte, calor extremo, riesgo
de helada, racha seca) se derivan en `services/weather.py` con umbrales
explicables: cada alerta dice qué dato la disparó.

### Correo saliente

`services/email.py` usa `smtplib` (biblioteca estándar, sin dependencia nueva).
Sin `AGROTRACE_SMTP_HOST` configurado, los correos se registran en el log en vez
de enviarse — la app funciona igual, solo que el mensaje no sale de verdad. Se
usa para dos cosas:

- **Notificar al productor** cuando un comprador le escribe desde el pasaporte
  público (`routes/passport.py::create_inquiry`).
- **Recuperar contraseña**: el enlace vence en 1 hora y es de un solo uso — el
  token crudo nunca se guarda, solo su huella SHA-256
  (`services/password_reset.py`).

Todos los envíos se hacen con `BackgroundTasks` de FastAPI, nunca dentro del
ciclo de petición-respuesta: SMTP es E/S bloqueante y no debe retrasar la
respuesta al usuario que disparó el correo.

### Directorio público

`GET /public/directory` lista los lotes que su dueño marcó explícitamente como
visibles (`Product.directory_listed`, opt-in por lote desde el detalle del
lote). Sin autenticación — es la puerta de entrada para un comprador que no
tiene el QR de un lote en particular.

### Insignia de certificación publicable

El diagnóstico de certificación (ver más abajo) es privado por defecto. El
productor puede elegir publicar, por estándar, una insignia compacta en el
pasaporte público: solo el veredicto y el puntaje del intento **más reciente**
para ese estándar — nunca las brechas críticas ni la hoja de ruta, que siguen
siendo siempre privadas. Al repetir el diagnóstico y mejorar el puntaje, la
insignia se actualiza sola, sin que el productor tenga que volver a publicar.

---

## API

Base: `/api/v1`. Documentación completa y navegable en `/docs`.

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/auth/register` · `/auth/login` | Registro e inicio de sesión (JWT) |
| `GET` | `/auth/me` | Perfil del usuario autenticado |
| `POST` | `/auth/forgot-password` · `/auth/reset-password` | Recuperar contraseña por correo |
| `GET/POST/PATCH/DELETE` | `/farms[/{id}]` | Fincas del usuario |
| `GET/POST/PATCH/DELETE` | `/products[/{id}]` | Lotes trazables |
| `GET/POST` | `/products/{id}/events` | Cadena de eventos |
| `GET` | `/products/{id}/verify` | Verificación de integridad |
| `GET` | `/products/{id}/qr.png` | QR del pasaporte |
| `GET` | `/products/{id}/reporte.pdf` | Reporte de trazabilidad en PDF |
| `POST/DELETE` | `/products/{id}/photos[/{photo_id}]` | Fotos de evidencia |
| `GET` | `/farms/{id}/clima` | Pronóstico y alertas climáticas |
| `GET/POST/DELETE` | `/inquiries[...]` | Bandeja de mensajes de compradores |
| `GET` | `/media/photos/{archivo}` | Entrega de fotos (sin auth) |
| `GET` | `/dashboard/summary` | Agregados del panel |
| `POST` | `/ai/products/{id}/story` | Agente de narrativa |
| `POST` | `/ai/products/{id}/export-sheet` | Agente de exportación |
| `POST` | `/ai/products/{id}/insights` | Agente agronómico |
| `POST` | `/ai/assistant` | Asistente conversacional |
| `GET` | `/ai/status` · `/ai/runs` | Estado y bitácora de la IA |
| `POST` | `/products/{id}/certification/publish` | Publicar/retirar insignia de certificación en el pasaporte |
| `GET` | `/public/passport/{public_id}` | **Pasaporte público** (sin auth) |
| `POST` | `/public/passport/{public_id}/contacto` | Mensaje de un comprador (sin auth, con límite por IP) |
| `GET` | `/public/directory` | **Directorio público** de lotes (sin auth) |

Todo lo que cuelga de `/farms`, `/products`, `/dashboard` y `/ai` exige token y
está filtrado por propietario: un usuario nunca alcanza lotes de otro.

---

## Diseño

Dirección **agro-editorial cálida**. Tipografías: **Fraunces** (display),
**Inter Tight** (texto) e **IBM Plex Mono** (hashes e identificadores).

Los tokens viven en [`frontend/src/styles/tokens.css`](frontend/src/styles/tokens.css).
Los colores de estado están verificados para contraste AA sobre las superficies
crema y blanca, y la integridad de la cadena nunca se comunica solo por color:
siempre lleva icono y etiqueta.

---

## Comandos útiles

```bash
# backend
python -m uvicorn app.main:app --reload --port 8000
python -m ruff check app

# frontend
npm run dev          # desarrollo
npm run build        # build de producción
npm run typecheck    # solo TypeScript
```

Para empezar de cero, borra `backend/agrotrace.db` y reinicia: se vuelve a sembrar
la cuenta de demostración.
