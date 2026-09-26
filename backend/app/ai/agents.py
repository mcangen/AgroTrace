"""Los agentes de IA de AgroTrace.

Cada agente arma su contexto desde los datos reales del producto y su cadena de
trazabilidad, llama a Gemini con salida estructurada y persiste el resultado en
el pasaporte. Cada ejecucion queda registrada en `AgentRun` para que el panel
muestre la actividad de IA real y no una animacion.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai import fallbacks
from app.ai.client import GeminiResult, gemini
from app.ai.schemas import (
    CertificationRoadmapOutput,
    ExportSheetOutput,
    InsightsOutput,
    StoryOutput,
)
from app.models import (
    AgentKind,
    AgentRun,
    AgentStatus,
    Product,
    ProductPassport,
    TraceEvent,
)
from app.services.certification_data import CertStandardDef
from app.services.certification_scoring import ScoringResult

log = logging.getLogger(__name__)

STORYTELLING_SYSTEM = """Eres el agente de narrativa de AgroTrace, una plataforma \
de trazabilidad para pequenos productores agricolas colombianos.

Escribes historias de origen para compradores internacionales e importadores.
Reglas:
- Usa unicamente los datos verificados que te entregan. Nunca inventes \
certificaciones, premios, analisis de laboratorio ni cifras que no aparezcan.
- Tono calido y concreto, no publicitario. Nada de superlativos vacios.
- La version en ingles debe sonar natural para un comprador anglofono, no una \
traduccion literal.
- Menciona el lugar y al menos un dato real del proceso registrado."""

EXPORT_SYSTEM = """Eres el agente de documentacion de exportacion de AgroTrace.

Produces fichas tecnicas para importadores de producto agricola colombiano.
Reglas:
- Solo datos verificables presentes en la cadena de trazabilidad entregada.
- Prioriza: variedad, altitud, fechas, metodo de proceso, rendimiento, humedad.
- Si un dato no esta disponible, omitelo en lugar de estimarlo.
- Registro profesional y sobrio, apto para documentacion comercial."""

INSIGHTS_SYSTEM = """Eres el agente agronomico de AgroTrace.

Analizas la cadena de eventos de un lote y das recomendaciones accionables al \
productor.
Reglas:
- Fundamenta cada hallazgo en un evento concreto de la cadena o en su ausencia.
- Senala vacios de registro (etapas faltantes, intervalos anomalos entre eventos).
- `severity` debe ser exactamente uno de: info, oportunidad, riesgo.
- El puntaje de calidad refleja la completitud y consistencia de la trazabilidad, \
no una evaluacion sensorial del producto.
- Habla en espanol, directo y sin tecnicismos innecesarios."""

ASSISTANT_SYSTEM = """Eres el asistente de AgroTrace. Respondes preguntas del \
productor sobre sus lotes, su trazabilidad y como mejorar su posicion comercial.

Reglas:
- Responde solo con base en el contexto entregado. Si el dato no esta, dilo \
claramente y sugiere que evento registrar para obtenerlo.
- Respuestas breves: maximo 4 oraciones, en espanol.
- No inventes hashes, fechas ni cifras."""

CERTIFICATION_SYSTEM = """Eres el agente de certificaciones de AgroTrace. \
Escribes hojas de ruta para que un lote avance hacia una certificacion \
(Fairtrade o Rainforest Alliance) a partir de un diagnostico ya calculado \
por reglas y de la cadena de trazabilidad real del lote.

Reglas:
- Usa solo los datos del diagnostico y la cadena de trazabilidad entregados.
- Prioriza primero los requisitos criticos sin cumplir, luego las brechas de \
mayor peso.
- Cada paso debe ser una accion concreta y verificable, no un consejo generico.
- Cruza la cadena de eventos real: si el lote ya tiene evidencia de una \
practica (ej. eventos de control fitosanitario sin quimicos), reconocelo en \
vez de pedir "empezar" algo que ya existe.
- No inventes plazos legales ni nombres de certificadoras que no esten en el \
contexto.
- `priority` debe ser exactamente uno de: critico, alto, medio."""


# ---------------------------------------------------------------------------
# Contexto
# ---------------------------------------------------------------------------


def _event_line(event: TraceEvent) -> str:
    try:
        data = json.loads(event.payload or "{}")
    except json.JSONDecodeError:
        data = {"raw": event.payload}
    fields = ", ".join(f"{k}: {v}" for k, v in data.items() if v not in (None, "", []))
    fecha = event.occurred_at.date().isoformat() if event.occurred_at else "sin fecha"
    linea = f"- [{fecha}] {event.event_type.value}"
    if fields:
        linea += f" — {fields}"
    if event.note:
        linea += f" (nota: {event.note})"
    return linea


def _certification_gap_lines(
    standard_def: CertStandardDef, answers: dict[str, str]
) -> list[str]:
    """Solo las respuestas que no fueron 'si', con el texto real de la opcion
    elegida (no solo 'no'/'parcial') -- mantiene el prompt corto incluso con
    las ~30 preguntas de Rainforest Alliance, sin perder la brecha exacta."""
    lines: list[str] = []
    for section in standard_def.sections:
        for question in section.questions:
            value = answers.get(question.id, "no")
            if value == "yes":
                continue
            label = next(
                (opt.label for opt in question.options if opt.value == value), value
            )
            marker = " [CRITICO]" if question.critical else ""
            lines.append(f"- [{section.name}] {question.text} -> {label}{marker}")
    return lines


def build_context(product: Product, events: list[TraceEvent]) -> str:
    """Texto plano con todo lo verificado del lote. Es el unico insumo del modelo."""
    farm = product.farm
    lines = [
        "=== FICHA DEL LOTE (datos verificados) ===",
        f"Producto: {product.name}",
        f"Variedad: {product.variety or 'no registrada'}",
        f"Estado: {product.status.value}",
        f"Finca: {farm.name}",
        f"Productor: {farm.owner_name or 'no registrado'}",
        f"Ubicacion: {farm.location}",
        f"Altitud: {farm.altitude_m} msnm" if farm.altitude_m else "Altitud: no registrada",
        f"Area de la finca: {farm.area_ha} ha" if farm.area_ha else "Area: no registrada",
        f"Siembra: {product.planting_date or 'no registrada'}",
        f"Cosecha: {product.harvest_date or 'no registrada'}",
        f"Insumos: {product.insumos or 'no registrados'}",
        f"Post-cosecha: {product.post_cosecha or 'no registrado'}",
        f"Responsable: {product.responsable or 'no registrado'}",
        "",
        f"=== CADENA DE TRAZABILIDAD ({len(events)} eventos sellados) ===",
    ]
    lines.extend(_event_line(e) for e in events)
    if not events:
        lines.append("- (sin eventos registrados)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Bitacora
# ---------------------------------------------------------------------------


def _log_run(
    db: Session,
    *,
    product_id: int | None,
    agent: AgentKind,
    result: GeminiResult,
    used_fallback: bool,
) -> AgentRun:
    if used_fallback:
        status = AgentStatus.ERROR if result.error else AgentStatus.FALLBACK
    else:
        status = AgentStatus.OK
    run = AgentRun(
        product_id=product_id,
        agent=agent,
        status=status,
        model=result.model,
        latency_ms=result.latency_ms,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        detail=result.error,
    )
    db.add(run)
    return run


def _ensure_passport(db: Session, product: Product) -> ProductPassport:
    if product.passport is not None:
        return product.passport
    passport = ProductPassport(product_id=product.id, public_id=product.public_id)
    db.add(passport)
    db.flush()
    product.passport = passport
    return passport


def _stamp(passport: ProductPassport, result: GeminiResult, used_fallback: bool) -> None:
    if not used_fallback:
        passport.ai_model = result.model
        passport.ai_generated_at = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Agentes
# ---------------------------------------------------------------------------


def run_storytelling(
    db: Session, product: Product, events: list[TraceEvent]
) -> tuple[StoryOutput, bool]:
    """Devuelve (salida, vino_del_modelo)."""
    result = gemini.generate(
        system=STORYTELLING_SYSTEM,
        prompt=(
            f"{build_context(product, events)}\n\n"
            "Escribe la historia de origen de este lote."
        ),
        schema=StoryOutput,
        temperature=0.85,
    )

    output = result.parsed if result.ok and result.parsed else None
    used_fallback = output is None
    if used_fallback:
        log.info("Storytelling en respaldo para producto %s: %s", product.id, result.error)
        output = fallbacks.story(product.name, product.farm.name, product.farm.location)

    passport = _ensure_passport(db, product)
    passport.story_es = output.story_es
    passport.story_en = output.story_en
    passport.tasting_notes = output.tasting_notes
    _stamp(passport, result, used_fallback)
    _log_run(
        db,
        product_id=product.id,
        agent=AgentKind.STORYTELLING,
        result=result,
        used_fallback=used_fallback,
    )
    db.commit()
    return output, not used_fallback


def run_export_sheet(
    db: Session, product: Product, events: list[TraceEvent]
) -> tuple[ExportSheetOutput, bool]:
    """Devuelve (salida, vino_del_modelo)."""
    result = gemini.generate(
        system=EXPORT_SYSTEM,
        prompt=(
            f"{build_context(product, events)}\n\n"
            "Genera la ficha tecnica de exportacion bilingue de este lote."
        ),
        schema=ExportSheetOutput,
        temperature=0.4,
    )

    output = result.parsed if result.ok and result.parsed else None
    used_fallback = output is None
    if used_fallback:
        log.info("Ficha export en respaldo para producto %s: %s", product.id, result.error)
        output = fallbacks.export_sheet(product.name, product.farm.name, product.farm.location)

    passport = _ensure_passport(db, product)
    passport.export_title_es = output.title_es
    passport.export_title_en = output.title_en
    passport.export_body_es = output.body_es
    passport.export_body_en = output.body_en
    _stamp(passport, result, used_fallback)
    _log_run(
        db,
        product_id=product.id,
        agent=AgentKind.EXPORT_SHEET,
        result=result,
        used_fallback=used_fallback,
    )
    db.commit()
    return output, not used_fallback


def run_insights(
    db: Session, product: Product, events: list[TraceEvent]
) -> tuple[InsightsOutput, bool]:
    """Devuelve (salida, vino_del_modelo)."""
    result = gemini.generate(
        system=INSIGHTS_SYSTEM,
        prompt=(
            f"{build_context(product, events)}\n\n"
            "Analiza la trazabilidad de este lote y entrega tus hallazgos."
        ),
        schema=InsightsOutput,
        temperature=0.5,
        model=None,
    )

    output = result.parsed if result.ok and result.parsed else None
    used_fallback = output is None
    if used_fallback:
        log.info("Insights en respaldo para producto %s: %s", product.id, result.error)
        output = fallbacks.insights(len(events), configured=gemini.enabled)

    _log_run(
        db,
        product_id=product.id,
        agent=AgentKind.INSIGHTS,
        result=result,
        used_fallback=used_fallback,
    )
    db.commit()
    return output, not used_fallback


def run_assistant(db: Session, context: str, question: str) -> tuple[str, bool]:
    """Responde una pregunta abierta sobre la finca. Devuelve (respuesta, es_respaldo)."""
    result = gemini.generate(
        system=ASSISTANT_SYSTEM,
        prompt=f"{context}\n\n=== PREGUNTA DEL PRODUCTOR ===\n{question}",
        temperature=0.6,
        max_output_tokens=600,
    )

    used_fallback = not (result.ok and result.text)
    answer = (
        fallbacks.assistant_unavailable(configured=gemini.enabled)
        if used_fallback
        else (result.text or "").strip()
    )

    _log_run(
        db,
        product_id=None,
        agent=AgentKind.ASSISTANT,
        result=result,
        used_fallback=used_fallback,
    )
    db.commit()
    return answer, used_fallback


def run_certification_roadmap(
    db: Session,
    product: Product,
    events: list[TraceEvent],
    standard_def: CertStandardDef,
    scoring: ScoringResult,
    answers: dict[str, str],
) -> tuple[CertificationRoadmapOutput, bool]:
    """Devuelve (salida, vino_del_modelo).

    A diferencia de los demas agentes, NO hace `db.commit()`: quien llama
    (el router de certificacion) todavia tiene que completar los campos de
    `roadmap_summary`/`roadmap_steps` en la fila de `CertificationAssessment`
    antes de guardar, asi que el commit final le corresponde a el -- una sola
    transaccion cubre tanto el assessment como esta bitacora.
    """
    gap_lines = _certification_gap_lines(standard_def, answers)
    crit_note = (
        f"{len(scoring.critical_gaps)} requisito(s) critico(s) sin cumplir"
        if scoring.critical_gaps
        else "ningun requisito critico pendiente"
    )
    diagnosis = "\n".join(
        [
            f"=== DIAGNOSTICO DE CERTIFICACION: {standard_def.name} ===",
            f"Puntaje global: {scoring.overall_score}% | Veredicto: {scoring.verdict.value} "
            f"| {crit_note}",
            "",
            "Respuestas que no fueron 'si' (posibles brechas), por seccion:",
            *(gap_lines or ["- (todas las respuestas fueron afirmativas)"]),
        ]
    )

    result = gemini.generate(
        system=CERTIFICATION_SYSTEM,
        prompt=(
            f"{build_context(product, events)}\n\n{diagnosis}\n\n"
            "Escribe la hoja de ruta personalizada para que este lote avance "
            f"hacia la certificacion {standard_def.name}."
        ),
        schema=CertificationRoadmapOutput,
        temperature=0.5,
    )

    output = result.parsed if result.ok and result.parsed else None
    used_fallback = output is None
    if used_fallback:
        log.info(
            "Certificacion en respaldo para producto %s (%s): %s",
            product.id,
            standard_def.key.value,
            result.error,
        )
        output = fallbacks.certification_roadmap(
            standard_def, scoring, configured=gemini.enabled
        )

    _log_run(
        db,
        product_id=product.id,
        agent=AgentKind.CERTIFICATION,
        result=result,
        used_fallback=used_fallback,
    )
    return output, not used_fallback
