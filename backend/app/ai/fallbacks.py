"""Contenido de respaldo cuando Gemini no esta disponible.

Se construye con los datos reales del producto para que la app siga siendo util
sin API key, y para que quede claro en la UI que es un texto generico.
"""

from __future__ import annotations

from app.ai.schemas import (
    CertificationRoadmapOutput,
    ExportSheetOutput,
    InsightItem,
    InsightsOutput,
    RoadmapStepOutput,
    StoryOutput,
)
from app.models import CertificationVerdict
from app.services.certification_data import CertStandardDef
from app.services.certification_scoring import ScoringResult


def story(product_name: str, farm_name: str, location: str) -> StoryOutput:
    place = location or "Colombia"
    return StoryOutput(
        story_es=(
            f"En {place}, la finca {farm_name} cultiva {product_name.lower()} con practicas "
            "que se transmiten de generacion en generacion. Cada etapa del proceso queda "
            "registrada y sellada criptograficamente, desde la siembra hasta el despacho. "
            "Detras de este producto hay una historia de tierra, familia y trabajo verificable."
        ),
        story_en=(
            f"In {place}, {farm_name} grows {product_name.lower()} using practices passed "
            "down through generations. Every stage is recorded and cryptographically sealed, "
            "from planting to shipping. Behind this product lies a verifiable story of land, "
            "family and work."
        ),
        tasting_notes="Perfil de origen unico, trazabilidad verificada",
    )


def export_sheet(product_name: str, farm_name: str, location: str) -> ExportSheetOutput:
    place = location or "Colombia"
    return ExportSheetOutput(
        title_es=f"{product_name} — {farm_name}",
        title_en=f"{product_name} — {farm_name}",
        body_es=(
            f"Producto de origen unico cultivado en {place}. Cadena de custodia completa "
            "registrada evento por evento y verificable mediante hashes SHA-256 encadenados. "
            "Documentacion de trazabilidad disponible para importadores."
        ),
        body_en=(
            f"Single-origin product grown in {place}. Full chain of custody recorded event "
            "by event and verifiable through chained SHA-256 hashes. Traceability "
            "documentation available for importers."
        ),
    )


def insights(event_count: int, configured: bool = False) -> InsightsOutput:
    """Respaldo del agente agronomico.

    `configured` distingue los dos motivos por los que se llega aqui: no haber
    puesto la API key, o que el modelo no respondiera. Decirle al usuario que
    configure una key que ya tiene solo lo confunde.
    """
    if configured:
        why = (
            "El modelo no respondio esta vez; vuelve a intentarlo en un momento."
        )
        detail = (
            "El servicio de Gemini rechazo la peticion o se quedo sin tiempo. "
            "Revisa la bitacora de agentes en el panel para ver el error exacto."
        )
    else:
        why = "Conecta una API key de Gemini para obtener un analisis agronomico detallado."
        detail = (
            "Configura GEMINI_API_KEY en backend/.env para que el agente analice "
            "la cadena de eventos y genere recomendaciones especificas."
        )

    return InsightsOutput(
        summary=(
            f"El lote tiene {event_count} evento(s) registrado(s) y su cadena es integra. {why}"
        ),
        quality_score=4.0,
        items=[
            InsightItem(
                title="Analisis de IA no disponible",
                detail=detail,
                severity="info",
            ),
            InsightItem(
                title="Mantener la cadencia de registro",
                detail=(
                    "Registrar cada labor el mismo dia en que ocurre mejora la calidad de "
                    "la trazabilidad y la confianza del comprador."
                ),
                severity="oportunidad",
            ),
            InsightItem(
                title="Completar datos del lote",
                detail=(
                    "Variedad, fechas de siembra y cosecha e insumos empleados son los "
                    "campos que mas piden los importadores."
                ),
                severity="oportunidad",
            ),
        ],
    )


_VERDICT_LABELS = {
    CertificationVerdict.READY: "listo para iniciar auditoría",
    CertificationVerdict.ALMOST_READY: "casi listo, con brechas por cerrar",
    CertificationVerdict.NOT_READY: "aún no listo",
}
_STAGE_PRIORITY = {"warn": "alto", "active": "alto", "done": "medio"}


def certification_roadmap(
    standard_def: CertStandardDef, scoring: ScoringResult, configured: bool = False
) -> CertificationRoadmapOutput:
    """Respaldo del agente de certificacion.

    No es un texto generico: cita el score, el veredicto real y, si hay
    requisitos criticos sin cumplir, los enumera uno por uno con el texto
    exacto de la pregunta que fallo -- eso ya es una hoja de ruta especifica
    a este intento, aunque no la haya escrito un modelo. El roadmap estatico
    del legacy se agrega como apoyo adicional.
    """
    gap_steps = [
        RoadmapStepOutput(
            title=f"Resolver requisito crítico {gap.id}",
            detail=(
                f"Tu respuesta actual no cumple: “{gap.text}”. Es un requisito "
                f"eliminatorio de {standard_def.name}."
            ),
            priority="critico",
        )
        for gap in scoring.critical_gaps
    ]
    stage_steps = [
        RoadmapStepOutput(
            title=stage.title,
            detail=f"{stage.etapa}: " + "; ".join(stage.tasks),
            priority=_STAGE_PRIORITY.get(stage.type, "medio"),
        )
        for stage in standard_def.fallback_roadmap
    ]

    # Con brechas criticas, esas son la prioridad; el roadmap completo solo
    # aporta contexto adicional (3 primeras etapas). Sin brechas criticas
    # (ALMOST_READY o READY) no hay nada puntual que senalar, asi que se
    # muestra el roadmap completo.
    steps = gap_steps + stage_steps[:3] if gap_steps else stage_steps

    if configured:
        why = "El modelo no respondió esta vez; vuelve a intentarlo en un momento."
    else:
        why = "Conecta una API key de Gemini para una hoja de ruta personalizada según tu cadena de trazabilidad."

    gaps_note = (
        f" Tiene {len(scoring.critical_gaps)} requisito(s) crítico(s) sin cumplir."
        if scoring.critical_gaps
        else ""
    )
    summary = (
        f"Diagnóstico para {standard_def.name}: {scoring.overall_score}% de cumplimiento, "
        f"{_VERDICT_LABELS[scoring.verdict]}.{gaps_note} {why}"
    )

    return CertificationRoadmapOutput(summary=summary, steps=steps)


def assistant_unavailable(configured: bool = False) -> str:
    if configured:
        return (
            "No pude consultar el modelo en este momento: el servicio rechazo la "
            "peticion o se agoto el tiempo de espera. Intentalo de nuevo en unos "
            "segundos. Mientras tanto puedes revisar la cadena de eventos y el "
            "pasaporte del producto en el panel."
        )
    return (
        "El asistente necesita una API key de Gemini para responder. Configura "
        "GEMINI_API_KEY en backend/.env y reinicia el servidor. Mientras tanto puedes "
        "consultar la cadena de eventos y el pasaporte del producto en el panel."
    )
