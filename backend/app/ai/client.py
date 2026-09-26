"""Cliente unico sobre el SDK `google-genai`.

El mismo SDK habla con la Gemini Developer API (API key) y con Vertex AI
(project + location + Application Default Credentials). Aqui se decide cual usar
en funcion de la configuracion, de modo que migrar a Vertex sea cambiar variables
de entorno y no codigo.

Todas las llamadas devuelven un `GeminiResult`, que nunca lanza: si no hay
credenciales o el modelo falla, el llamador recibe `ok=False` y decide su
contenido de respaldo. Los agentes nunca deben tumbar una peticion HTTP.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from app.core.config import settings

log = logging.getLogger(__name__)

# Fallos pasajeros del servicio: conviene reintentar en vez de caer al respaldo.
# Los modelos flash populares devuelven 503 con bastante frecuencia en horas pico.
TRANSIENT_MARKERS = (
    "503",
    "UNAVAILABLE",
    "429",
    "RESOURCE_EXHAUSTED",
    "500",
    "INTERNAL",
    "DEADLINE_EXCEEDED",
    "timeout",
)


def _is_transient(error: str) -> bool:
    upper = error.upper()
    return any(marker.upper() in upper for marker in TRANSIENT_MARKERS)


@dataclass(slots=True)
class GeminiResult:
    ok: bool
    text: str | None = None
    parsed: Any | None = None
    model: str | None = None
    latency_ms: int = 0
    tokens_in: int | None = None
    tokens_out: int | None = None
    error: str | None = None


class GeminiClient:
    """Envoltorio perezoso: el SDK solo se importa e instancia si hay credenciales."""

    def __init__(self) -> None:
        self._client: Any | None = None
        self._types: Any | None = None
        self._init_error: str | None = None
        self._initialized = False

    # -- infraestructura ----------------------------------------------------

    @property
    def enabled(self) -> bool:
        return settings.ai_enabled

    @property
    def backend(self) -> str:
        return "vertex-ai" if settings.use_vertex else "gemini-api"

    def _ensure_client(self) -> bool:
        if self._initialized:
            return self._client is not None
        self._initialized = True

        if not settings.ai_enabled:
            self._init_error = (
                "Falta GEMINI_API_KEY (o AGROTRACE_GCP_PROJECT si usas Vertex AI)."
            )
            return False

        try:
            from google import genai
            from google.genai import types

            # timeout va en milisegundos y acota cada llamada individual, para
            # que un modelo lento no consuma el presupuesto de los reintentos.
            http_options = types.HttpOptions(
                timeout=settings.gemini_timeout_seconds * 1000
            )

            if settings.use_vertex:
                self._client = genai.Client(
                    vertexai=True,
                    project=settings.gcp_project,
                    location=settings.gcp_location,
                    http_options=http_options,
                )
            else:
                self._client = genai.Client(
                    api_key=settings.gemini_api_key, http_options=http_options
                )
            self._types = types
            log.info("Gemini listo (backend=%s)", self.backend)
            return True
        except Exception as exc:  # pragma: no cover - depende del entorno
            self._init_error = f"No se pudo inicializar el SDK de Gemini: {exc}"
            log.warning(self._init_error)
            self._client = None
            return False

    def status(self) -> dict[str, Any]:
        """Estado que el frontend muestra en el panel de IA."""
        ready = self._ensure_client()
        return {
            "enabled": ready,
            "backend": self.backend,
            "model": settings.gemini_model,
            "model_pro": settings.gemini_model_pro,
            "reason": None if ready else self._init_error,
        }

    # -- generacion ---------------------------------------------------------

    def generate(
        self,
        *,
        system: str,
        prompt: str,
        schema: type[BaseModel] | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1200,
        model: str | None = None,
    ) -> GeminiResult:
        """Genera texto libre, o JSON validado si se pasa `schema`.

        Con `schema` usamos la salida estructurada nativa de Gemini
        (response_schema), que garantiza JSON con la forma pedida. Es mas fiable
        que pedirlo en el prompt y luego parsear a mano.

        Ante un fallo transitorio reintenta con espera creciente y, si el modelo
        principal sigue sin responder, prueba el de respaldo antes de rendirse.
        """
        primary = model or settings.gemini_model
        candidates = [primary]
        if settings.gemini_model_fallback and settings.gemini_model_fallback != primary:
            candidates.append(settings.gemini_model_fallback)

        last: GeminiResult | None = None
        deadline = time.monotonic() + settings.gemini_deadline_seconds

        for candidate in candidates:
            for attempt in range(1, max(1, settings.gemini_max_retries) + 1):
                if time.monotonic() >= deadline:
                    log.warning(
                        "Gemini agoto el presupuesto de %ss; se usara el respaldo",
                        settings.gemini_deadline_seconds,
                    )
                    return last or GeminiResult(
                        ok=False,
                        error=(
                            f"El modelo no respondio dentro de "
                            f"{settings.gemini_deadline_seconds}s."
                        ),
                        model=candidate,
                    )

                last = self._attempt(
                    system=system,
                    prompt=prompt,
                    schema=schema,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                    model=candidate,
                )
                if last.ok or not _is_transient(last.error or ""):
                    break

                # Espera exponencial con jitter, recortada al tiempo que queda.
                remaining = deadline - time.monotonic()
                if attempt < settings.gemini_max_retries and remaining > 0:
                    delay = min((2 ** (attempt - 1)) + random.uniform(0, 0.4), remaining)
                    log.info(
                        "Gemini %s no disponible (intento %d/%d), reintentando en %.1fs",
                        candidate,
                        attempt,
                        settings.gemini_max_retries,
                        delay,
                    )
                    time.sleep(delay)

            if last and last.ok:
                if candidate != primary:
                    log.warning("Gemini respondio con el modelo de respaldo %s", candidate)
                return last

        return last or GeminiResult(ok=False, error="Sin respuesta del modelo.", model=primary)

    def _attempt(
        self,
        *,
        system: str,
        prompt: str,
        schema: type[BaseModel] | None,
        temperature: float,
        max_output_tokens: int,
        model: str,
    ) -> GeminiResult:
        """Una sola llamada al modelo, sin politica de reintentos."""
        started = time.perf_counter()
        chosen_model = model

        if not self._ensure_client():
            return GeminiResult(ok=False, error=self._init_error, model=chosen_model)

        assert self._client is not None and self._types is not None
        types = self._types

        config_kwargs: dict[str, Any] = {
            "system_instruction": system,
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
        }
        if schema is not None:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = schema

        try:
            response = self._client.models.generate_content(
                model=chosen_model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            )
        except Exception as exc:
            latency = int((time.perf_counter() - started) * 1000)
            log.warning("Gemini fallo (%s): %s", chosen_model, exc)
            return GeminiResult(
                ok=False, error=str(exc), model=chosen_model, latency_ms=latency
            )

        latency = int((time.perf_counter() - started) * 1000)
        usage = getattr(response, "usage_metadata", None)

        parsed = getattr(response, "parsed", None) if schema is not None else None
        text = getattr(response, "text", None)

        if schema is not None and parsed is None and text:
            # El SDK no siempre puebla `.parsed`; reintentamos validando el texto.
            try:
                parsed = schema.model_validate_json(text)
            except Exception as exc:
                return GeminiResult(
                    ok=False,
                    error=f"Respuesta JSON invalida: {exc}",
                    model=chosen_model,
                    latency_ms=latency,
                    text=text,
                )

        if schema is None and not (text and text.strip()):
            return GeminiResult(
                ok=False,
                error="El modelo devolvio una respuesta vacia.",
                model=chosen_model,
                latency_ms=latency,
            )

        return GeminiResult(
            ok=True,
            text=text,
            parsed=parsed,
            model=chosen_model,
            latency_ms=latency,
            tokens_in=getattr(usage, "prompt_token_count", None) if usage else None,
            tokens_out=getattr(usage, "candidates_token_count", None) if usage else None,
        )


gemini = GeminiClient()
