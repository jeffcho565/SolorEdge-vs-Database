"""
Roof & Building Suitability — OpenStreetMap Overpass API.

Not all buildings can host a data center.  Retail spaces (Costco, Target,
malls) have open floor plates designed for shoppers, no raised floors, no
redundant power panels, and active tenants who cannot be displaced easily.

Warehouses, factories, and offices, by contrast, often already have:
  - Large, clear-span interior space
  - Heavy floor load capacity
  - Three-phase power feeds
  - Loading docks (for equipment delivery)

Source: OpenStreetMap Overpass API (free, no key required)
"""

import httpx
from src.models import CriterionResult

WEIGHT = 0.15
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# DC suitability by OSM building tag (higher = better for data center)
_DC_SCORES: dict[str, float] = {
    "data_center": 100,
    "server_farm": 100,
    "warehouse": 92,
    "industrial": 90,
    "factory": 88,
    "storage": 85,
    "office": 72,
    "commercial": 62,
    "mixed_use": 55,
    "civic": 50,
    "government": 50,
    "yes": 48,          # generic OSM tag — we don't know the type
    "": 45,
    "hotel": 35,
    "retail": 18,
    "supermarket": 14,
    "mall": 12,
    "shop": 14,
    "apartments": 18,
    "residential": 15,
    "house": 10,
    "dormitory": 15,
    "church": 20,
    "school": 22,
    "hospital": 30,
}

# Amenity tags that override and signal retail/public use
_RETAIL_AMENITIES = {
    "supermarket", "marketplace", "fast_food", "restaurant", "cafe",
    "bar", "pub", "food_court", "nightclub",
}


async def get_building_type_score(lat: float, lon: float) -> CriterionResult:
    try:
        query = f"""
[out:json][timeout:12];
(
  way["building"](around:80,{lat},{lon});
  relation["building"](around:80,{lat},{lon});
);
out tags;
"""
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            resp.raise_for_status()
            elements = resp.json().get("elements", [])

        if not elements:
            return CriterionResult(
                name="Roof & Building Suitability",
                score=45.0,
                weight=WEIGHT,
                weighted_contribution=round(45 * WEIGHT, 2),
                description=(
                    "Retail and residential buildings cannot be repurposed as data centers; "
                    "industrial/warehouse spaces are ideal"
                ),
                details="No building found in OpenStreetMap at this location — score is neutral",
                data_available=True,
            )

        tags = elements[0].get("tags", {})
        building_tag = tags.get("building", "").lower()
        amenity = tags.get("amenity", "").lower()
        shop = tags.get("shop", "")
        name = tags.get("name", "unnamed building")

        # Retail amenity/shop overrides the building tag
        if shop or amenity in _RETAIL_AMENITIES:
            score = 14.0
            type_label = shop or amenity
        else:
            score = _DC_SCORES.get(building_tag, 45.0)
            type_label = building_tag or "unknown"

        suitability = (
            "Ideal" if score >= 80
            else "Suitable" if score >= 60
            else "Marginal" if score >= 35
            else "Not suitable (great solar candidate instead)"
        )

        return CriterionResult(
            name="Roof & Building Suitability",
            score=round(score, 1),
            weight=WEIGHT,
            weighted_contribution=round(score * WEIGHT, 2),
            description=(
                "Retail and residential buildings cannot be repurposed as data centers; "
                "industrial/warehouse spaces are ideal"
            ),
            details=f'"{name}" — OSM type: {type_label} — {suitability}',
            data_available=True,
        )

    except Exception as exc:
        return CriterionResult(
            name="Roof & Building Suitability",
            score=45.0,
            weight=WEIGHT,
            weighted_contribution=round(45 * WEIGHT, 2),
            description=(
                "Retail and residential buildings cannot be repurposed as data centers; "
                "industrial/warehouse spaces are ideal"
            ),
            details=f"OSM data unavailable ({exc!s:.80}); neutral score applied",
            data_available=False,
        )
