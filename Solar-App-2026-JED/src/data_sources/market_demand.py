"""
Market & Location Demand — US Census Bureau ACS 5-Year Estimates.

Edge data centers are built for density: they serve the end users and devices
physically closest to them.  A facility in a rural county with 20,000 residents
captures a tiny addressable market; one in a metro area of 5 million can serve
millions of streaming sessions, IoT devices, and enterprise VPN connections.

Population is used as a proxy for:
  - Volume of latency-sensitive traffic (gaming, video conferencing, CDN)
  - Enterprise customer density (cloud workloads, colocation demand)
  - Hyperscaler PoP justification (AWS/Azure/GCP edge node placement)

Source: US Census Bureau ACS 5-Year Estimates API (free, no key required)
"""

import httpx
from src.models import CriterionResult

WEIGHT = 0.05
CENSUS_ACS_URL = "https://api.census.gov/data/2022/acs/acs5"
CENSUS_COORD_URL = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
_HEADERS = {"User-Agent": "SolarLandscapeHackathon/1.0"}


async def _get_fips(client: httpx.AsyncClient, lat: float, lon: float) -> tuple[str, str]:
    resp = await client.get(
        CENSUS_COORD_URL,
        params={
            "x": lon,
            "y": lat,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "format": "json",
        },
        headers=_HEADERS,
    )
    resp.raise_for_status()
    counties = (
        resp.json()
        .get("result", {})
        .get("geographies", {})
        .get("Counties", [])
    )
    if not counties:
        raise ValueError("County not found")
    return counties[0]["STATE"], counties[0]["COUNTY"]


def _pop_to_score(pop: int) -> tuple[float, str]:
    if pop >= 5_000_000:
        return 100.0, "Mega Metro (5M+)"
    elif pop >= 2_000_000:
        return 90.0, "Major Metro (2–5M)"
    elif pop >= 1_000_000:
        return 78.0, "Large Metro (1–2M)"
    elif pop >= 500_000:
        return 63.0, "Medium Metro (500K–1M)"
    elif pop >= 200_000:
        return 48.0, "Small Metro (200–500K)"
    elif pop >= 75_000:
        return 33.0, "Micropolitan (75–200K)"
    else:
        return 16.0, "Rural (<75K)"


async def get_market_demand_score(
    lat: float,
    lon: float,
    state_fips: str | None = None,
    county_fips: str | None = None,
) -> CriterionResult:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if not (state_fips and county_fips):
                state_fips, county_fips = await _get_fips(client, lat, lon)

            resp = await client.get(
                CENSUS_ACS_URL,
                params={
                    "get": "B01003_001E,NAME",
                    "for": f"county:{county_fips}",
                    "in": f"state:{state_fips}",
                },
                headers=_HEADERS,
            )
            resp.raise_for_status()
            rows = resp.json()

        if len(rows) < 2:
            raise ValueError("No ACS data returned")

        population = int(rows[1][0])
        county_name = rows[1][1]
        score, tier = _pop_to_score(population)

        return CriterionResult(
            name="Market & Location Demand",
            score=score,
            weight=WEIGHT,
            weighted_contribution=round(score * WEIGHT, 2),
            description=(
                "County population as a proxy for the addressable market for "
                "low-latency edge computing services"
            ),
            details=f"{county_name} — Population: {population:,} ({tier})",
            data_available=True,
        )

    except Exception as exc:
        return CriterionResult(
            name="Market & Location Demand",
            score=50.0,
            weight=WEIGHT,
            weighted_contribution=round(50 * WEIGHT, 2),
            description=(
                "County population as a proxy for the addressable market for "
                "low-latency edge computing services"
            ),
            details=f"Census data unavailable ({exc!s:.80}); neutral score applied",
            data_available=False,
        )
