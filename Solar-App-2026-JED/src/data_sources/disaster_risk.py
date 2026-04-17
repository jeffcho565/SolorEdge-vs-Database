"""
Climate Resilience — USGS Seismic API + Geographic Hazard Model.

Data centers require 99.999% uptime (~5 minutes of downtime per year).
Natural disasters are the most catastrophic threat to this target.

This module builds a composite disaster risk score from three components:

1. SEISMIC RISK (35%): USGS Earthquake Hazards API
   Counts M≥4.0 earthquakes within 200 km over 25 years.
   Source: https://earthquake.usgs.gov/fdsnws/event/1/ (public, no key)

2. TROPICAL / WIND RISK (40%): State/regional classification
   Based on FEMA historical disaster declaration frequency and NOAA
   hurricane track historical data. Captures hurricane, tornado, and
   straight-line wind threats.

3. FLOOD / PRECIP RISK (25%): Open-Meteo annual precipitation proxy
   High annual precipitation correlates with elevated flood risk.
   Source: https://archive-api.open-meteo.com (public, no key)

The component scores are INVERTED before being summed so that
higher score = safer = better for a data center.
"""

import asyncio
import math
import httpx
from src.models import CriterionResult

WEIGHT = 0.18

USGS_COUNT_URL = "https://earthquake.usgs.gov/fdsnws/event/1/count"
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"

# State-level wind/tropical hazard score (0=very risky, 100=very safe)
# Derived from FEMA major disaster declaration frequency 2000-2024 and
# NOAA hurricane/tornado climatology.
_STATE_WIND_SCORE: dict[str, float] = {
    # Extremely high risk: Gulf/Atlantic coasts + Tornado Alley
    "Florida":        5,   "Texas":          10,  "Louisiana":      10,
    "Mississippi":    12,  "Alabama":        15,  "Oklahoma":       12,
    "Kansas":         15,  "Missouri":       20,  "Arkansas":       18,
    # High risk
    "North Carolina": 25,  "South Carolina": 25,  "Georgia":        28,
    "Tennessee":      30,  "Virginia":       35,  "Nebraska":       30,
    "Iowa":           30,  "Indiana":        35,  "Ohio":           35,
    # Moderate risk
    "New Jersey":     42,  "New York":       45,  "Maryland":       45,
    "Delaware":       45,  "Pennsylvania":   48,  "Kentucky":       40,
    "Minnesota":      40,  "Wisconsin":      42,  "Michigan":       45,
    "Illinois":       38,  "West Virginia":  50,  "Connecticut":    50,
    "Rhode Island":   50,  "Massachusetts":  48,
    # Lower risk
    "Maine":          60,  "New Hampshire":  62,  "Vermont":        65,
    "Colorado":       60,  "Utah":           65,  "Nevada":         70,
    "Arizona":        68,  "New Mexico":     62,
    # Low risk
    "California":     72,  "Oregon":         75,  "Washington":     72,
    "Idaho":          78,  "Montana":        75,  "Wyoming":        75,
    "North Dakota":   55,  "South Dakota":   55,
    # Special
    "Alaska":         50,  "Hawaii":         55,
    "District of Columbia": 45,
}
_DEFAULT_WIND_SCORE = 45.0


def _seismic_count_to_score(count: int) -> float:
    """Fewer significant earthquakes near the site = safer = higher score."""
    if count == 0:
        return 95.0
    elif count <= 2:
        return 82.0
    elif count <= 10:
        return 62.0
    elif count <= 30:
        return 40.0
    elif count <= 100:
        return 22.0
    else:
        return 8.0


def _precip_to_flood_score(annual_mm: float) -> float:
    """Lower precipitation = lower flood risk = higher score."""
    if annual_mm < 300:
        return 95.0   # arid / semi-arid
    elif annual_mm < 500:
        return 82.0
    elif annual_mm < 800:
        return 68.0
    elif annual_mm < 1100:
        return 52.0
    elif annual_mm < 1500:
        return 35.0
    else:
        return 18.0   # very wet (Pacific NW, Gulf Coast)


async def _fetch_seismic(lat: float, lon: float) -> tuple[float, str]:
    """USGS earthquake count — returns (score, detail_label)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                USGS_COUNT_URL,
                params={
                    "format": "geojson",
                    "starttime": "2000-01-01",
                    "endtime": "2025-01-01",
                    "latitude": lat,
                    "longitude": lon,
                    "maxradiuskm": 200,
                    "minmagnitude": 4.0,
                },
            )
            count = resp.json().get("count", 0)
            return _seismic_count_to_score(count), f"Seismic: {count} M≥4 quake(s) within 200 km (25 yr)"
    except Exception as exc:
        return 50.0, f"Seismic: data unavailable ({exc!s:.40})"


async def _fetch_precipitation(lat: float, lon: float) -> tuple[float, str]:
    """Open-Meteo annual precipitation — returns (score, detail_label)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                OPEN_METEO_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "daily": "precipitation_sum",
                    "timezone": "auto",
                },
            )
            precip_list = resp.json().get("daily", {}).get("precipitation_sum", [])
            annual_mm = sum(p for p in precip_list if p is not None)
            return _precip_to_flood_score(annual_mm), f"Flood proxy: {annual_mm:.0f} mm/yr precipitation"
    except Exception as exc:
        return 50.0, f"Flood proxy: unavailable ({exc!s:.40})"


async def get_disaster_risk_score(
    lat: float,
    lon: float,
    state_name: str | None = None,
) -> CriterionResult:
    # Component 2 is a static lookup — instant
    wind_score = _STATE_WIND_SCORE.get(state_name or "", _DEFAULT_WIND_SCORE)

    # Components 1 and 3 are I/O-bound — run in parallel
    (seismic_score, seismic_label), (flood_score, flood_label) = await asyncio.gather(
        _fetch_seismic(lat, lon),
        _fetch_precipitation(lat, lon),
    )

    composite = seismic_score * 0.35 + wind_score * 0.40 + flood_score * 0.25

    return CriterionResult(
        name="Climate Resilience",
        score=round(composite, 1),
        weight=WEIGHT,
        weighted_contribution=round(composite * WEIGHT, 2),
        description=(
            "Composite natural disaster risk: seismic frequency (USGS), "
            "wind/hurricane exposure, and flood-proxy precipitation — "
            "higher score = safer site"
        ),
        details=" | ".join([seismic_label, f"Wind/Hurricane: state score {wind_score:.0f}/100", flood_label]),
        data_available=True,
    )
