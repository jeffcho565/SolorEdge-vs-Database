"""
Network Connectivity — US Census Bureau ACS 5-Year Estimates.

The FCC National Broadband Map API requires Akamai bot-manager session cookies
and cannot be called directly from a server-side script.  We use an equally
valid — and arguably more stable — proxy: the Census Bureau's ACS broadband
adoption rate for the county.

Counties with high broadband adoption have dense, competitive ISP markets with
fiber infrastructure.  A county where 92 % of households have broadband (like
Manhattan) is structurally different from one at 54 % — the former can support
the gigabit uplinks a data center needs; the latter likely cannot.

Variable B28002_007E = "Households with broadband internet (any type)"
Variable B28002_001E = "Total households"

Source: US Census Bureau ACS 5-Year Estimates API (free, no key required)
"""

import httpx
from src.models import CriterionResult

WEIGHT = 0.20
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


def _adoption_to_score(adoption_pct: float) -> tuple[float, str]:
    """Convert broadband adoption % to a 0–100 DC feasibility score."""
    if adoption_pct >= 90:
        return 95.0, f"{adoption_pct:.1f}% — Excellent (fiber-dense metro)"
    elif adoption_pct >= 82:
        return 80.0, f"{adoption_pct:.1f}% — Strong broadband market"
    elif adoption_pct >= 73:
        return 63.0, f"{adoption_pct:.1f}% — Adequate coverage"
    elif adoption_pct >= 62:
        return 45.0, f"{adoption_pct:.1f}% — Moderate coverage"
    elif adoption_pct >= 50:
        return 28.0, f"{adoption_pct:.1f}% — Limited coverage"
    else:
        return 12.0, f"{adoption_pct:.1f}% — Poor coverage (rural)"


async def get_broadband_score(
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
                    "get": "B28002_007E,B28002_001E,NAME",
                    "for": f"county:{county_fips}",
                    "in": f"state:{state_fips}",
                },
                headers=_HEADERS,
            )
            resp.raise_for_status()
            rows = resp.json()

        if len(rows) < 2:
            raise ValueError("No ACS data returned")

        broadband_hh = int(rows[1][0])
        total_hh = int(rows[1][1])
        county_name = rows[1][2]

        if total_hh == 0:
            raise ValueError("Zero households — bad data")

        adoption_pct = broadband_hh / total_hh * 100
        score, tier_label = _adoption_to_score(adoption_pct)

        return CriterionResult(
            name="Network Connectivity",
            score=round(score, 1),
            weight=WEIGHT,
            weighted_contribution=round(score * WEIGHT, 2),
            description=(
                "County-level broadband adoption rate (Census ACS) — a proxy for ISP "
                "market density and fiber infrastructure that data centers depend on"
            ),
            details=f"{county_name}: {tier_label} ({broadband_hh:,} of {total_hh:,} households)",
            data_available=True,
        )

    except Exception as exc:
        return CriterionResult(
            name="Network Connectivity",
            score=50.0,
            weight=WEIGHT,
            weighted_contribution=round(50 * WEIGHT, 2),
            description=(
                "County-level broadband adoption rate (Census ACS) — a proxy for ISP "
                "market density and fiber infrastructure that data centers depend on"
            ),
            details=f"Census ACS data unavailable ({exc!s:.80}); neutral score applied",
            data_available=False,
        )
