"""Formas de salida que se le exigen a Gemini via `response_schema`."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StoryOutput(BaseModel):
    story_es: str = Field(description="Historia de origen en espanol, 3 a 4 oraciones.")
    story_en: str = Field(description="La misma historia en ingles natural, no literal.")
    tasting_notes: str = Field(
        description="Notas sensoriales o de calidad, separadas por comas. Maximo 12 palabras."
    )


class ExportSheetOutput(BaseModel):
    title_es: str = Field(description="Titulo comercial corto en espanol.")
    title_en: str = Field(description="Titulo comercial corto en ingles.")
    body_es: str = Field(description="Ficha tecnica en espanol, 3 a 4 oraciones con datos concretos.")
    body_en: str = Field(description="La misma ficha tecnica en ingles.")


class InsightItem(BaseModel):
    title: str = Field(description="Titulo de la recomendacion, maximo 8 palabras.")
    detail: str = Field(description="Explicacion accionable en 1 o 2 oraciones.")
    severity: str = Field(description="Uno de: info, oportunidad, riesgo.")


class InsightsOutput(BaseModel):
    summary: str = Field(description="Diagnostico general del lote en 2 oraciones.")
    quality_score: float = Field(description="Puntaje de calidad estimado de 0 a 5.")
    items: list[InsightItem] = Field(description="Entre 3 y 5 hallazgos.")


class RoadmapStepOutput(BaseModel):
    title: str = Field(description="Titulo de la accion, maximo 10 palabras.")
    detail: str = Field(description="Que hacer concretamente, 1-2 oraciones.")
    priority: str = Field(description="Uno de: critico, alto, medio.")


class CertificationRoadmapOutput(BaseModel):
    summary: str = Field(
        description="Diagnostico personalizado en 2-3 oraciones, citando el estado real del lote."
    )
    steps: list[RoadmapStepOutput] = Field(description="Entre 4 y 8 pasos ordenados por prioridad.")
