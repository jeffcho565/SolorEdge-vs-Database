"""
Core evaluation orchestrator.

Flow:
  1. Geocode the address → lat/lon + FIPS codes
  2. Fetch all 6 criteria in parallel (asyncio.gather)
  3. Compute weighted Data Center score (normalising if data is missing)
  4. Compute independent Solar score
  5. Generate recommendation + narrative
"""

import asyncio
from src.models import EvaluationResult, GeoLocation, CriterionResult

_BUILDING_CRITERION = "Roof & Building Suitability"
from src.data_sources.geocoding import geocode_address
from src.data_sources.broadband import get_broadband_score
from src.data_sources.disaster_risk import get_disaster_risk_score
from src.data_sources.climate import get_climate_score, temp_to_solar_climate_score
from src.data_sources.building_type import get_building_type_score
from src.data_sources.ixp_proximity import get_ixp_proximity_score
from src.data_sources.market_demand import get_market_demand_score
from src.data_sources.renewable_energy import get_renewable_energy_score
from src.data_sources.solar_policy import get_solar_policy


# ---------------------------------------------------------------------------
# Solar score helpers
# ---------------------------------------------------------------------------

_SOLAR_BUILDING_SCORES: dict[str, float] = {
    # Large flat commercial roofs → ideal solar surface
    "retail": 95,
    "supermarket": 95,
    "mall": 92,
    "warehouse": 88,
    "industrial": 85,
    "storage": 82,
    "factory": 80,
    "office": 62,
    "commercial": 68,
    "mixed_use": 55,
    "yes": 50,
    "": 48,
    "data_center": 45,
    "server_farm": 40,
    "hotel": 52,
    "apartments": 35,
    "residential": 28,
    "house": 18,
}


def _solar_building_score_from_dc(dc_building_score: float) -> float:
    """
    Convert a DC building score to a solar building score.

    Key insight: the buildings worst for DC (retail, score ~15) have the
    largest flat roofs and are therefore best for solar (score ~95).
    Warehouses are good for BOTH (DC: 92, solar: 88).
    """
    if dc_building_score <= 20:    # retail/residential — bad DC, great solar
        return 92.0
    elif dc_building_score <= 35:  # hotel/mixed — mediocre DC, decent solar
        return 60.0
    elif dc_building_score <= 60:  # generic/commercial
        return 55.0
    elif dc_building_score <= 75:  # office
        return 62.0
    else:                          # warehouse/industrial — good DC AND solar
        return 85.0


def _compute_solar_score(criteria: list[CriterionResult], avg_temp_f: float = 60.0) -> float:
    """
    Solar feasibility score (0–100) using three independent components:
      - Building suitability for rooftop solar (40 %)
      - Solar irradiance proxy: warmer climate = more sun (35 %)
      - Site safety / disaster risk (25 %) — protects long-lived asset
    """
    scores = {c.name: c for c in criteria}

    building_dc = scores.get(_BUILDING_CRITERION)
    building_solar = _solar_building_score_from_dc(
        building_dc.score if building_dc else 48.0
    )

    solar_climate = temp_to_solar_climate_score(avg_temp_f)

    disaster = scores.get("Climate Resilience")
    disaster_score = disaster.score if (disaster and disaster.data_available) else 50.0

    return round(
        building_solar * 0.40 + solar_climate * 0.35 + disaster_score * 0.25,
        1,
    )


# ---------------------------------------------------------------------------
# Recommendation + narrative
# ---------------------------------------------------------------------------

def _confidence(diff: float) -> str:
    if abs(diff) >= 20:
        return "strong"
    elif abs(diff) >= 10:
        return "moderate"
    else:
        return "weak"


def _narrative(
    dc_score: float,
    solar_score: float,
    criteria: list[CriterionResult],
    recommendation: str,
) -> str:
    top = sorted(
        [c for c in criteria if c.data_available], key=lambda c: c.score, reverse=True
    )
    bottom = sorted([c for c in criteria if c.data_available], key=lambda c: c.score)

    if recommendation == "data_center":
        opener = (
            f"With a data center feasibility score of {dc_score:.0f}/100, "
            f"this location is a stronger candidate for an edge data center "
            f"than for rooftop solar ({solar_score:.0f}/100)."
        )
    else:
        opener = (
            f"This location scores {dc_score:.0f}/100 for edge data center feasibility "
            f"but {solar_score:.0f}/100 for rooftop solar — making it a better "
            f"candidate for Solar Landscape's rooftop solar programme."
        )

    strength = ""
    if top:
        s = top[0]
        strength = f" Its strongest asset is {s.name} (score {s.score:.0f}/100): {s.details}."

    concern = ""
    if bottom and bottom[0].score < 50:
        w = bottom[0]
        concern = f" The key limiting factor is {w.name} (score {w.score:.0f}/100): {w.details}."

    solar_pitch = ""
    if recommendation == "solar":
        solar_pitch = (
            " Solar Landscape can install a rooftop array here that generates "
            "predictable lease income for the building owner with zero capital outlay "
            "— a more reliable return than an uncertain data center conversion."
        )

    return opener + strength + concern + solar_pitch


# ---------------------------------------------------------------------------
# Flip insight
# ---------------------------------------------------------------------------

def _flip_insight(
    criteria: list[CriterionResult],
    dc_score: float,
    solar_score: float,
    recommendation: str,
) -> str:
    """Compute a plain-English explanation of what single change would flip the recommendation."""
    diff = round(abs(dc_score - solar_score), 1)
    available = [c for c in criteria if c.data_available]

    if recommendation == "solar":
        # Find criteria that, if scored 100, would flip DC above solar
        flippers = []
        for c in available:
            gain = (100.0 - c.score) * c.weight
            if dc_score + gain > solar_score:
                flippers.append((c, gain))

        if flippers:
            c, gain = min(flippers, key=lambda x: x[1])
            return (
                f"Flip to Data Center: if {c.name} reached excellent "
                f"(currently {c.score:.0f}/100), DC score rises ~{gain:.0f} pts "
                f"({dc_score:.0f} → {dc_score + gain:.0f}), surpassing solar ({solar_score:.0f}). "
                f"Real-world path: fiber upgrades, IXP co-location, or grid modernisation."
            )
        else:
            top2 = sorted(available, key=lambda c: (100.0 - c.score) * c.weight, reverse=True)[:2]
            combined = sum((100.0 - c.score) * c.weight for c in top2)
            names = " + ".join(c.name for c in top2)
            return (
                f"No single improvement flips this — solar leads by {diff:.0f} pts. "
                f"Even maximising {names} adds only ~{combined:.0f} pts combined "
                f"({dc_score + combined:.0f} vs solar's {solar_score:.0f}). "
                f"This is a genuine solar-first location."
            )

    else:  # data_center wins
        weakest = min(available, key=lambda c: c.score) if available else None
        if diff >= 20:
            extra = f" Even if {weakest.name} ({weakest.score:.0f}/100) improved to excellent, the DC lead holds." if weakest else ""
            return (
                f"Strong DC advantage of {diff:.0f} pts.{extra} "
                f"Solar Landscape can still pitch a shared-revenue rooftop array as a secondary income stream."
            )
        else:
            lever = f"{weakest.name} ({weakest.score:.0f}/100)" if weakest else "key criteria"
            return (
                f"Narrow DC lead of {diff:.0f} pts. If {lever} deteriorates or the "
                f"building converts to retail/residential use, solar could flip ahead. "
                f"Both options have merit — consider a dual-pitch lease negotiation."
            )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def evaluate_address(address: str) -> EvaluationResult:
    # Step 1 — geocode
    location: GeoLocation = await geocode_address(address)

    # Step 2 — fetch all criteria in parallel
    criteria: tuple[CriterionResult, ...] = await asyncio.gather(
        get_ixp_proximity_score(location.lat, location.lon),
        get_broadband_score(location.lat, location.lon, location.state_fips, location.county_fips),
        get_renewable_energy_score(location.state),
        get_disaster_risk_score(location.lat, location.lon, location.state),
        get_building_type_score(location.lat, location.lon),
        get_climate_score(location.lat, location.lon),
        get_market_demand_score(
            location.lat, location.lon, location.state_fips, location.county_fips
        ),
    )
    criteria_list = list(criteria)

    # Step 2b — residential override
    # If Nominatim identified this as a home address, force the building
    # suitability score to near-zero (houses cannot host data centers) and
    # flag the result so the UI can warn the user.
    address_warning: str | None = None
    if location.is_residential:
        address_warning = (
            "This address appears to be a residential property. "
            "Edge data centers require commercial or industrial buildings. "
            "Scores below reflect that; the solar score may still be relevant "
            "if the property has suitable roof space."
        )
        criteria_list = [
            c if c.name != _BUILDING_CRITERION
            else CriterionResult(
                name=_BUILDING_CRITERION,
                score=5.0,
                weight=c.weight,
                weighted_contribution=round(5.0 * c.weight, 2),
                description=c.description,
                details="Residential property — not suitable for data center conversion",
                data_available=True,
            )
            for c in criteria_list
        ]

    # Step 3 — data center score (weight-normalised)
    available = [c for c in criteria_list if c.data_available]
    total_weight_avail = sum(c.weight for c in available)
    total_weight_all = sum(c.weight for c in criteria_list)

    if total_weight_avail == 0:
        dc_score = 50.0
    else:
        # Weighted sum over available, scaled by proportion of weight covered
        weighted_sum = sum(c.score * c.weight for c in available)
        dc_score = round(weighted_sum / total_weight_all, 1)

    # Step 4 — solar score
    climate_result = next(
        (c for c in criteria_list if c.name == "Cooling & Power Density"), None
    )
    # Extract average temperature from the details string if available
    avg_temp_f = 60.0  # default
    if climate_result and climate_result.data_available:
        try:
            detail = climate_result.details
            # "2023 avg temperature: 54.3°F — ..."
            avg_temp_f = float(detail.split(":")[1].split("°")[0].strip())
        except Exception:
            pass

    solar_score = _compute_solar_score(criteria_list, avg_temp_f)

    # Step 5 — recommendation
    diff = dc_score - solar_score
    recommendation = "data_center" if diff >= 0 else "solar"
    confidence = _confidence(diff)

    # Step 6 — strengths / weaknesses
    sorted_avail = sorted(available, key=lambda c: c.score, reverse=True)
    key_strengths = [
        f"{c.name}: {c.score:.0f}/100 — {c.details}"
        for c in sorted_avail[:2]
        if c.score >= 65
    ]
    key_weaknesses = [
        f"{c.name}: {c.score:.0f}/100 — {c.details}"
        for c in reversed(sorted_avail)
        if c.score < 50
    ][:2]

    narrative = _narrative(dc_score, solar_score, criteria_list, recommendation)

    return EvaluationResult(
        address=address,
        location=location,
        overall_score=dc_score,
        solar_score=solar_score,
        recommendation=recommendation,
        recommendation_confidence=confidence,
        criteria=criteria_list,
        narrative=narrative,
        key_strengths=key_strengths,
        key_weaknesses=key_weaknesses,
        data_sources_available=len(criteria_list),
        data_sources_total=len(criteria_list),
        address_warning=address_warning,
        flip_insight=_flip_insight(criteria_list, dc_score, solar_score, recommendation),
        solar_policy=get_solar_policy(location.state),
    )
