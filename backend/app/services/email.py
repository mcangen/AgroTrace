"""Envio de correo saliente.

Usa `smtplib` de la libreria estandar -- no hace falta agregar una dependencia
nueva para algo tan acotado como mandar notificaciones y enlaces de
recuperacion. Sin `AGROTRACE_SMTP_HOST` configurado, `send()` registra el
correo en el log y devuelve False en vez de fallar: la aplicacion sigue
funcionando igual, solo que el mensaje no sale de verdad (mismo principio que
el respaldo de Gemini cuando falta la API key).

Las llamadas a `send()` se hacen siempre desde una `BackgroundTask` de FastAPI,
nunca dentro del ciclo de peticion-respuesta: SMTP es E/S bloqueante y no debe
retrasar la respuesta al usuario que disparo el correo.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

log = logging.getLogger(__name__)


def send(to: str, subject: str, text_body: str, html_body: str | None = None) -> bool:
    """Envia un correo. Devuelve True si de verdad salio por SMTP."""
    if not settings.email_enabled:
        log.info(
            "Correo no enviado (SMTP no configurado) -- para: %s | asunto: %s\n%s",
            to,
            subject,
            text_body,
        )
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
        return True
    except Exception as exc:
        # Un correo que no sale nunca debe tumbar la peticion que lo origino.
        log.warning("No se pudo enviar el correo a %s: %s", to, exc)
        return False
