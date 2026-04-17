"""
Cooling & Power Density — Open-Meteo Historical Weather API.

Cooling accounts for 30–40 % of a data center's total energy consumption.
Cooler ambient temperatures dramatically reduce this burden:
  - Every 1°F reduction in average temperature saves ~1 % in cooling energy
  - Data centers in Iceland/Nordic countries save 40 %+ vs. US Sun Belt

Also computes a solar_climate_score (warmer + sunnier = better for solar).

Source: Open-Meteo Archive API (free, no key required)
"""

import httpx
from src.models import CriterionResult

WEIGHT = 0.07
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"


def _temp_to_dc_score(avg_f: float) -> float:
    """Higher score = cooler = lower cooling costs = better for DC."""
    if avg_f < 40:
        return 100
    elif avg_f < 50:
        return 90
    elif avg_f < 58:
        return 78
    elif avg_f < 65:
        return 62
    elif avg_f < 72:
        return 45
    elif avg_f < 80:
        return 28
    else:
        return 12


def temp_to_solar_climate_score(avg_f: float) -> float:
    """Warmer climates correlate with higher solar irradiance (rough proxy)."""
    if avg_f >= 72:
        return 100
    elif avg_f >= 65:
        return 85
    elif avg_f >= 58:
        return 68
    elif avg_f >= 50:
        return 50
    elif avg_f >= 40:
        return 32
    else:
        return 18


async def get_climate_score(lat: float, lon: float) -> CriterionResult:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                OPEN_METEO_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "daily": "temperature_2m_mean",
                    "temperature_unit": "fahrenheit",
                    "timezone": "auto",
                },
            )
            resp.raise_for_status()
            daily = resp.json().get("daily", {})
            temps = [t for t in daily.get("temperature_2m_mean", []) if t is not None]

        if not temps:
            raise ValueError("No temperature data in response")

        avg_f = sum(temps) / len(temps)
        score = _temp_to_dc_score(avg_f)

        tier = (
            "Excellent (Nordic-class cooling)"
            if score >= 85
            else "Good"
            if score >= 65
            else "Moderate"
            if score >= 45
            else "High cooling cost"
        )

        return CriterionResult(
            name="Cooling & Power Density",
            score=round(score, 1),
            weight=WEIGHT,
            weighted_contribution=round(score * WEIGHT, 2),
            description=(
                "Ambient temperature drives cooling infrastructure costs; "
                "cooler climates can cut cooling energy 30–40 %"
            ),
            details=f"2023 avg temperature: {avg_f:.1f}°F — {tier}",
            data_available=True,
        )

    except Exception as exc:
        return CriterionResult(
            name="Cooling & Power Density",
            score=50.0,
            weight=WEIGHT,
            weighted_contribution=round(50 * WEIGHT, 2),
            description=(
                "Ambient temperature drives cooling infrastructure costs; "
                "cooler climates can cut cooling energy 30–40 %"
            ),
            details=f"Climate data unavailable ({exc!s:.80}); neutral score applied",
            data_available=False,
        )
