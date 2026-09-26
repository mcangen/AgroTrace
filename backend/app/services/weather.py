"""Pronostico y alertas climaticas por finca, sobre Open-Meteo.

Se eligio Open-Meteo porque no pide API key ni registro: una finca puede
consultar su clima sin que el productor tenga que gestionar credenciales de
otro servicio. Si el servicio no responde, el resto de la app no se entera --
los endpoints devuelven `None` y la interfaz simplemente no muestra el panel.

Las alertas no vienen del proveedor: se derivan aqui con umbrales pensados para
cultivo (lluvia fuerte antes de cosecha, calor extremo, frio cercano a helada,
racha seca). Eso las hace explicables -- cada alerta dice exactamente que dato
la disparo.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date

import httpx

log = logging.getLogger(__name__)

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SECONDS = 10.0

# Umbrales de alerta. Son deliberadamente conservadores y generales: AgroTrace
# no sabe que cultivo especifico tiene cada lote, asi que avisa de condiciones
# que importan a casi cualquiera y deja el juicio fino al productor.
HEAVY_RAIN_MM = 25.0
EXTREME_HEAT_C = 35.0
COLD_RISK_C = 4.0
DRY_SPELL_DAYS = 7


@dataclass
class WeatherDay:
    date: date
    temp_min: float | None
    temp_max: float | None
    precipitation_mm: float | None
    precipitation_probability: int | None


@dataclass
class WeatherAlert:
    severity: str  # 'riesgo' | 'aviso' | 'info'
    title: str
    detail: str


@dataclass
class WeatherReport:
    latitude: float
    longitude: float
    timezone: str
    days: list[WeatherDay] = field(default_factory=list)
    alerts: list[WeatherAlert] = field(default_factory=list)


def geocode(municipality: str, department: str | None, country: str | None) -> tuple[float, float] | None:
    """Resuelve coordenadas desde el nombre del municipio.

    Devuelve None si no hay coincidencia o si el servicio falla: geocodificar
    es una comodidad, nunca un requisito para guardar una finca.
    """
    if not municipality or not municipality.strip():
        return None

    params: dict[str, str | int] = {
        "name": municipality.strip(),
        "count": 10,
        "language": "es",
        "format": "json",
    }
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.get(GEOCODE_URL, params=params)
            response.raise_for_status()
            results = response.json().get("results") or []
    except Exception as exc:
        log.info("Geocodificacion fallida para %r: %s", municipality, exc)
        return None

    if not results:
        return None

    # Con varios homonimos (Ciénaga existe en Magdalena y en Boyacá), se
    # prefiere el que coincide con el departamento declarado por el productor.
    if department:
        needle = department.strip().lower()
        for item in results:
            admin1 = (item.get("admin1") or "").lower()
            if needle and (needle in admin1 or admin1 in needle):
                return float(item["latitude"]), float(item["longitude"])

    if country:
        needle_country = country.strip().lower()
        for item in results:
            if (item.get("country") or "").lower() == needle_country:
                return float(item["latitude"]), float(item["longitude"])

    first = results[0]
    return float(first["latitude"]), float(first["longitude"])


def forecast(latitude: float, longitude: float, days: int = 7) -> WeatherReport | None:
    """Pronostico diario + alertas derivadas. None si el servicio no responde."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
        "forecast_days": max(1, min(days, 16)),
        "timezone": "auto",
    }
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.get(FORECAST_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        log.info("Pronostico fallido para %s,%s: %s", latitude, longitude, exc)
        return None

    daily = data.get("daily") or {}
    times = daily.get("time") or []

    parsed: list[WeatherDay] = []
    for index, day in enumerate(times):
        parsed.append(
            WeatherDay(
                date=date.fromisoformat(day),
                temp_min=_at(daily.get("temperature_2m_min"), index),
                temp_max=_at(daily.get("temperature_2m_max"), index),
                precipitation_mm=_at(daily.get("precipitation_sum"), index),
                precipitation_probability=_at(daily.get("precipitation_probability_max"), index),
            )
        )

    return WeatherReport(
        latitude=float(data.get("latitude", latitude)),
        longitude=float(data.get("longitude", longitude)),
        timezone=str(data.get("timezone") or "UTC"),
        days=parsed,
        alerts=build_alerts(parsed),
    )


def build_alerts(days: list[WeatherDay]) -> list[WeatherAlert]:
    """Traduce el pronostico a avisos accionables para el productor."""
    alerts: list[WeatherAlert] = []
    if not days:
        return alerts

    for day in days:
        fecha = day.date.strftime("%d/%m")

        if day.precipitation_mm is not None and day.precipitation_mm >= HEAVY_RAIN_MM:
            alerts.append(
                WeatherAlert(
                    severity="riesgo",
                    title=f"Lluvia fuerte el {fecha}",
                    detail=(
                        f"Se esperan {day.precipitation_mm:.0f} mm. Si tienes cosecha o "
                        "secado al sol en esos dias, conviene adelantarlo o cubrir el producto."
                    ),
                )
            )

        if day.temp_max is not None and day.temp_max >= EXTREME_HEAT_C:
            alerts.append(
                WeatherAlert(
                    severity="aviso",
                    title=f"Calor extremo el {fecha}",
                    detail=(
                        f"Maxima de {day.temp_max:.0f} °C. Evita labores en las horas pico "
                        "y vigila el estres hidrico del cultivo."
                    ),
                )
            )

        if day.temp_min is not None and day.temp_min <= COLD_RISK_C:
            alerts.append(
                WeatherAlert(
                    severity="riesgo",
                    title=f"Riesgo de helada el {fecha}",
                    detail=(
                        f"Minima de {day.temp_min:.0f} °C. Considera proteger las plantas "
                        "sensibles durante la madrugada."
                    ),
                )
            )

    # Racha seca: se evalua sobre toda la ventana, no dia a dia.
    conocidos = [d for d in days if d.precipitation_mm is not None]
    if len(conocidos) >= DRY_SPELL_DAYS and all(d.precipitation_mm < 1.0 for d in conocidos):
        alerts.append(
            WeatherAlert(
                severity="aviso",
                title=f"Sin lluvia en {len(conocidos)} dias",
                detail=(
                    "El pronostico no registra lluvia significativa en toda la ventana. "
                    "Revisa el riego si tu cultivo depende de la lluvia."
                ),
            )
        )

    if not alerts:
        alerts.append(
            WeatherAlert(
                severity="info",
                title="Sin alertas para los proximos dias",
                detail="El pronostico no muestra condiciones que requieran accion inmediata.",
            )
        )

    return alerts


def _at(values: list | None, index: int):
    if not values or index >= len(values):
        return None
    return values[index]
