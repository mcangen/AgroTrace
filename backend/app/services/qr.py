"""Generacion del QR que lleva al pasaporte publico del producto."""

from __future__ import annotations

import io

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from app.core.config import settings


def passport_url(public_id: str) -> str:
    return f"{settings.public_web_url.rstrip('/')}/p/{public_id}"


def passport_qr_png(public_id: str, box_size: int = 10) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=2,
    )
    qr.add_data(passport_url(public_id))
    qr.make(fit=True)
    image = qr.make_image(fill_color="#12341f", back_color="#ffffff")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
