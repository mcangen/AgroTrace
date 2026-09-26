"""Cadena de hashes SHA-256 que sella los eventos de trazabilidad.

Cada evento encadena su payload con el `chain_hash` del evento anterior, de modo
que alterar un evento pasado invalida todos los posteriores. Es el mismo esquema
del proyecto original en Java, portado a Python sin cambios de formato para que
los hashes emitidos antes sigan siendo reproducibles.
"""

from __future__ import annotations

import hashlib

GENESIS = "GENESIS"


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def chain_hash(payload: str, prev_hash: str | None) -> str:
    """Hash que enlaza este payload con el eslabon anterior."""
    prev = prev_hash if prev_hash and prev_hash.strip() else GENESIS
    return _sha256_hex(f"{payload}|{prev}")


def payload_hash(payload: str) -> str:
    """Huella del payload aislado, independiente de su posicion en la cadena."""
    return _sha256_hex(f"{payload}|PAYLOAD_ONLY")
