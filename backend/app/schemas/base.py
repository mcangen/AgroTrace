"""Base compartida por los esquemas de salida que envuelven un modelo ORM.

Vive en su propio archivo (en vez de dentro de `schemas/__init__.py`) para que
otros modulos de `app.schemas` -- como `certification.py` -- puedan importarla
sin depender del orden de ejecucion de `__init__.py` ni arriesgar un import
circular.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
