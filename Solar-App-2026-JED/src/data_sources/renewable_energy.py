"""
Renewable Energy Access — state-level grid mix (EIA Electric Power Monthly, 2023).

Edge data centers increasingly compete on sustainability. Enterprise clients with
ESG commitments require operators to source from clean grids. A site in a state
where 60%+ of grid power is renewable can credibly offer carbon-neutral edge
compute without expensive off-site PPAs.

Higher score = cleaner grid = lower carbon footprint + long-term cost stability.

Source: US Energy Information Administration (EIA) Electric Power Monthly 2023
(Table 1.1 — Net Generation by Source, by State)
"""

from src.models import CriterionResult

WEIGHT = 0.13

# Approximate % of in-state electricity generation from renewables (EIA 2023)
# Includes hydro, wind, solar, geothermal, biomass — excludes nuclear
_STATE_RENEWABLE_PCT: dict[str, float] = {
    "Vermont":               99,
    "Washington":            82,
    "Maine":                 79,
    "South Dakota":          78,
    "Idaho":                 74,
    "Oregon":                64,
    "Montana":               63,
    "North Dakota":          62,
    "Iowa":                  59,
    "Oklahoma":              46,
    "Kansas":                48,
    "California":            50,
    "Minnesota":             38,
    "New Mexico":            37,
    "Colorado":              36,
    "New Hampshire":         33,
    "New York":              34,
    "Alaska":                33,
    "Hawaii":                30,
    "Texas":                 27,
    "Nebraska":              29,
    "Nevada":                28,
    "Arizona":               24,
    "Utah":                  23,
    "Massachusetts":         22,
    "Wisconsin":             14,
    "Illinois":              19,
    "Tennessee":             18,
    "Wyoming":               16,
    "Michigan":              13,
    "Maryland":              13,
    "Indiana":               13,
    "Arkansas":              14,
    "Missouri":              12,
    "Virginia":              15,
    "North Carolina":        12,
    "Pennsylvania":          11,
    "Connecticut":           12,
    "Rhode Island":          25,
    "New Jersey":             8,
    "Ohio":                   8,
    "Kentucky":              11,
    "South Carolina":         8,
    "Georgia":               10,
    "Florida":                8,
    "Alabama":               10,
    "West Virginia":          8,
    "Mississippi":            8,
    "Louisiana":              9,
    "Delaware":               5,
    "District of Columbia":   6,
}

_DEFAULT_PCT = 20.0


def _pct_to_score(pct: float) -> tuple[float, str]:
    if pct >= 75:
        return 100.0, "Exceptional — near-100% renewable grid"
    elif pct >= 55:
        return 85.0, "Excellent — majority renewable generation"
    elif pct >= 40:
        return 70.0, "Good — substantial renewable mix"
    elif pct >= 25:
        return 52.0, "Moderate — growing renewable share"
    elif pct >= 15:
        return 35.0, "Limited — fossil-fuel dominant grid"
    else:
        return 18.0, "Poor — heavily fossil-fuel dependent"


async def get_renewable_energy_score(state: str | None) -> CriterionResult:
    """
    Return a CriterionResult based on the state's renewable energy share.
    Fully synchronous (static lookup) wrapped in async for asyncio.gather().
    """
    pct = _STATE_RENEWABLE_PCT.get(state or "", _DEFAULT_PCT)
    score, label = _pct_to_score(pct)
    data_available = bool(state and state in _STATE_RENEWABLE_PCT)

    details = (
        f"{state or 'Unknown state'}: ~{pct:.0f}% renewable grid generation (EIA 2023) — {label}"
    )

    return CriterionResult(
        name="Renewable Energy Access",
        score=round(score, 1),
        weight=WEIGHT,
        weighted_contribution=round(score * WEIGHT, 2),
        description=(
            "State renewable share of grid electricity generation (EIA 2023) — "
            "cleaner grids lower operational carbon footprint and attract ESG-driven enterprise clients"
        ),
        details=details,
        data_available=data_available,
    )
