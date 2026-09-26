"""Reporte de trazabilidad en PDF, listo para enviar a un importador.

Se arma con ReportLab (puro Python, sin dependencias del sistema) para que el
backend siga corriendo igual en Windows, Linux o un contenedor.

El documento es deliberadamente sobrio: es un anexo comercial, no un folleto.
Lleva los hashes completos porque su razon de ser es que el comprador pueda
reconstruir la verificacion por su cuenta.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models import Product, ProductPassport, TraceEvent
from app.services.qr import passport_qr_png, passport_url

GREEN = colors.HexColor("#12341f")
GREEN_SOFT = colors.HexColor("#e6f4ea")
LINE = colors.HexColor("#d6dbd7")
MUTED = colors.HexColor("#5b6b5f")
DANGER = colors.HexColor("#b03a2e")

EVENT_LABELS = {
    "REGISTRO_INICIAL": "Registro inicial",
    "SIEMBRA": "Siembra",
    "LABOR_CULTURAL": "Labor cultural",
    "FERTILIZACION": "Fertilizacion",
    "CONTROL_FITOSANITARIO": "Control fitosanitario",
    "COSECHA": "Cosecha",
    "POST_COSECHA": "Post-cosecha",
    "SECADO": "Secado",
    "CONTROL_CALIDAD": "Control de calidad",
    "EMPAQUE": "Empaque",
    "CERTIFICACION": "Certificacion",
    "DESPACHO": "Despacho",
}


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontSize=20, textColor=GREEN, alignment=TA_LEFT,
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontSize=10.5, textColor=MUTED, spaceAfter=10
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontSize=12, textColor=GREEN, spaceBefore=14,
            spaceAfter=6,
        ),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=9.5, leading=14),
        "small": ParagraphStyle(
            "small", parent=base["Normal"], fontSize=8, textColor=MUTED, leading=11
        ),
        "mono": ParagraphStyle(
            "mono", parent=base["Normal"], fontName="Courier", fontSize=7, textColor=MUTED,
            leading=9,
        ),
    }


def build_traceability_report(
    product: Product,
    events: list[TraceEvent],
    verification: dict,
    passport: ProductPassport | None,
) -> bytes:
    """Genera el PDF completo y lo devuelve en memoria."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Trazabilidad - {product.name}",
        author="AgroTrace",
    )
    st = _styles()
    farm = product.farm
    story: list = []

    # --- Encabezado ---------------------------------------------------------
    story.append(Paragraph("AgroTrace &middot; Reporte de trazabilidad", st["small"]))
    story.append(Paragraph(_esc(product.name), st["title"]))
    story.append(
        Paragraph(
            f"{_esc(farm.name)} &mdash; {_esc(farm.location)}",
            st["subtitle"],
        )
    )

    # --- Estado de la cadena ------------------------------------------------
    valid = bool(verification.get("valid"))
    estado = "CADENA INTEGRA" if valid else "CADENA ALTERADA"
    estado_color = GREEN if valid else DANGER
    banner = Table(
        [[Paragraph(f"<b>{estado}</b>", st["body"]),
          Paragraph(_esc(str(verification.get("message", ""))), st["small"])]],
        colWidths=[38 * mm, None],
    )
    banner.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GREEN_SOFT if valid else colors.HexColor("#fbeae7")),
            ("TEXTCOLOR", (0, 0), (0, 0), estado_color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ])
    )
    story.append(banner)

    # --- Ficha del lote -----------------------------------------------------
    story.append(Paragraph("Ficha del lote", st["h2"]))
    ficha = [
        ("Producto", product.name),
        ("Variedad", product.variety or "no registrada"),
        ("Estado", product.status.value),
        ("Finca", farm.name),
        ("Productor", farm.owner_name or "no registrado"),
        ("Ubicacion", farm.location),
        ("Altitud", f"{farm.altitude_m} msnm" if farm.altitude_m else "no registrada"),
        ("Siembra", str(product.planting_date) if product.planting_date else "no registrada"),
        ("Cosecha", str(product.harvest_date) if product.harvest_date else "no registrada"),
        ("Insumos", product.insumos or "no registrados"),
        ("Post-cosecha", product.post_cosecha or "no registrado"),
        ("Identificador publico", product.public_id),
    ]
    story.append(_kv_table(ficha, st))

    # --- QR + enlace publico ------------------------------------------------
    qr_img = Image(BytesIO(passport_qr_png(product.public_id, box_size=6)), 30 * mm, 30 * mm)
    qr_block = Table(
        [[qr_img,
          Paragraph(
              "Escanea para abrir el pasaporte publico y verificar la cadena en linea:<br/>"
              f"<font face='Courier' size='7'>{_esc(passport_url(product.public_id))}</font>",
              st["small"],
          )]],
        colWidths=[34 * mm, None],
    )
    qr_block.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(Spacer(1, 8))
    story.append(qr_block)

    # --- Narrativa y ficha de exportacion -----------------------------------
    if passport and (passport.story_es or passport.export_body_es):
        story.append(Paragraph("Descripcion del producto", st["h2"]))
        if passport.export_title_es:
            story.append(Paragraph(f"<b>{_esc(passport.export_title_es)}</b>", st["body"]))
            story.append(Spacer(1, 4))
        if passport.export_body_es:
            story.append(Paragraph(_esc(passport.export_body_es), st["body"]))
            story.append(Spacer(1, 6))
        if passport.story_es:
            story.append(Paragraph(_esc(passport.story_es), st["body"]))
        if passport.ai_model:
            story.append(Spacer(1, 4))
            story.append(
                Paragraph(
                    f"Texto generado con IA ({_esc(passport.ai_model)}) a partir de los datos "
                    "verificados de la cadena.",
                    st["small"],
                )
            )

    # --- Cadena de eventos --------------------------------------------------
    story.append(Paragraph(f"Cadena de trazabilidad ({len(events)} eventos)", st["h2"]))
    story.append(
        Paragraph(
            "Cada evento se sella con SHA-256 sobre su contenido y el sello del evento "
            "anterior. Alterar cualquier evento pasado invalida todos los posteriores.",
            st["small"],
        )
    )
    story.append(Spacer(1, 6))

    broken_at = verification.get("broken_at_sequence")
    for event in events:
        story.append(_event_block(event, st, broken_at))

    # --- Pie ----------------------------------------------------------------
    generado = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Spacer(1, 14))
    story.append(
        Paragraph(
            f"Documento generado por AgroTrace el {generado}. "
            "Su contenido puede verificarse de forma independiente recalculando la cadena "
            "de hashes a partir del pasaporte publico.",
            st["small"],
        )
    )

    doc.build(story, onFirstPage=_page_furniture, onLaterPages=_page_furniture)
    return buffer.getvalue()


def _event_block(event: TraceEvent, st: dict, broken_at: int | None) -> KeepTogether:
    try:
        data = json.loads(event.payload or "{}")
    except json.JSONDecodeError:
        data = {}

    fotos = data.pop("fotos_sha256", None)
    campos = ", ".join(f"{k}: {v}" for k, v in data.items() if v not in (None, "", []))

    fecha = event.occurred_at.strftime("%Y-%m-%d") if event.occurred_at else "sin fecha"
    etiqueta = EVENT_LABELS.get(event.event_type.value, event.event_type.value)
    roto = broken_at is not None and event.sequence >= broken_at

    encabezado = f"<b>#{event.sequence} &middot; {_esc(etiqueta)}</b> &mdash; {fecha}"
    if event.recorded_by:
        encabezado += f" &middot; {_esc(event.recorded_by)}"
    if roto:
        encabezado += " &middot; <font color='#b03a2e'><b>[CADENA ROTA AQUI]</b></font>"

    partes = [Paragraph(encabezado, st["body"])]
    if campos:
        partes.append(Paragraph(_esc(campos), st["small"]))
    if event.note:
        partes.append(Paragraph(f"Nota: {_esc(event.note)}", st["small"]))
    if fotos:
        partes.append(
            Paragraph(f"Evidencia fotografica sellada: {len(fotos)} archivo(s)", st["small"])
        )
    partes.append(
        Paragraph(
            f"anterior {event.prev_hash}<br/>sello&nbsp;&nbsp;&nbsp;&nbsp; {event.chain_hash}",
            st["mono"],
        )
    )
    partes.append(Spacer(1, 7))
    return KeepTogether(partes)


def _kv_table(rows: list[tuple[str, str]], st: dict) -> Table:
    data = [
        [Paragraph(f"<b>{_esc(k)}</b>", st["small"]), Paragraph(_esc(str(v)), st["body"])]
        for k, v in rows
    ]
    table = Table(data, colWidths=[42 * mm, None])
    table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
        ])
    )
    return table


def _page_furniture(canvas, doc) -> None:
    """Linea y numero de pagina al pie, iguales en todas las paginas."""
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.4)
    canvas.line(20 * mm, 14 * mm, A4[0] - 20 * mm, 14 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 9.5 * mm, "AgroTrace - Trazabilidad agricola verificable")
    canvas.drawRightString(A4[0] - 20 * mm, 9.5 * mm, f"Pagina {doc.page}")
    canvas.restoreState()


def _esc(value: str) -> str:
    """Escapa lo que ReportLab interpretaria como marcado."""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
