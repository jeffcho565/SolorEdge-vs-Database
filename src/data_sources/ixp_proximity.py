"""
Internet Exchange Point (IXP) Proximity — a novel metric for edge data centers.

Edge data centers derive their value from ultra-low latency to end users AND
to the internet backbone. Every 100 miles from a major IXP adds ~1 ms of
latency — a meaningful penalty for latency-sensitive workloads (gaming, CDN,
real-time AI inference).

This module scores a location based on its distance to major US IXPs and
carrier-neutral colocation campuses (sources: PeeringDB, Equinix, CoreSite,
Switch public colocation directories).
"""

import math
from src.models import CriterionResult

WEIGHT = 0.22

# Major US internet exchange points and carrier-neutral colo hubs
US_IXPS = [
    {"name": "DE-CIX New York / Equinix NY",      "city": "New York, NY",      "lat": 40.7799, "lon": -74.0566},
    {"name": "CoreSite NY1",                        "city": "New York, NY",      "lat": 40.7580, "lon": -73.9855},
    {"name": "Equinix CH1/CH2",                     "city": "Chicago, IL",       "lat": 41.8781, "lon": -87.6298},
    {"name": "CoreSite CH1",                        "city": "Chicago, IL",       "lat": 41.8844, "lon": -87.6654},
    {"name": "Equinix DA1/DA2",                     "city": "Dallas, TX",        "lat": 32.7767, "lon": -96.7970},
    {"name": "CoreSite DE1",                        "city": "Denver, CO",        "lat": 39.7392, "lon": -104.9903},
    {"name": "Equinix SV1/SV5",                     "city": "San Jose, CA",      "lat": 37.3382, "lon": -121.8863},
    {"name": "Equinix LA1/LA2",                     "city": "Los Angeles, CA",   "lat": 34.0195, "lon": -118.4912},
    {"name": "Equinix MI1",                         "city": "Miami, FL",         "lat": 25.7617, "lon": -80.1918},
    {"name": "Equinix AT1",                         "city": "Atlanta, GA",       "lat": 33.7490, "lon": -84.3880},
    {"name": "Equinix SE2",                         "city": "Seattle, WA",       "lat": 47.6062, "lon": -122.3321},
    {"name": "Equinix DC2/DC10 (Ashburn)",          "city": "Ashburn, VA",       "lat": 39.0437, "lon": -77.4875},
    {"name": "CoreSite Boston",                     "city": "Boston, MA",        "lat": 42.3601, "lon": -71.0589},
    {"name": "Equinix PH1",                         "city": "Philadelphia, PA",  "lat": 39.9526, "lon": -75.1652},
    {"name": "Switch Las Vegas",                    "city": "Las Vegas, NV",     "lat": 36.1699, "lon": -115.1398},
    {"name": "Equinix HO2",                         "city": "Houston, TX",       "lat": 29.7604, "lon": -95.3698},
    {"name": "Equinix PX1",                         "city": "Phoenix, AZ",       "lat": 33.4484, "lon": -112.0740},
    {"name": "Corelink / Deft Minneapolis",         "city": "Minneapolis, MN",   "lat": 44.9778, "lon": -93.2650},
    {"name": "365 Main San Francisco",              "city": "San Francisco, CA", "lat": 37.7749, "lon": -122.4194},
    {"name": "Equinix SL1",                         "city": "Salt Lake City, UT","lat": 40.7608, "lon": -111.8910},
]


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3958.8  # Earth radius in miles
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


async def get_ixp_proximity_score(lat: float, lon: float) -> CriterionResult:
    """
    Score based on proximity to the nearest US Internet Exchange Point.

    This is a synchronous computation (no network calls) wrapped in an
    async interface so it can participate in asyncio.gather().
    """
    ranked = sorted(
        [(_haversine_miles(lat, lon, ixp["lat"], ixp["lon"]), ixp) for ixp in US_IXPS],
        key=lambda x: x[0],
    )
    nearest_dist, nearest_ixp = ranked[0]
    nearby_100mi = [(d, ixp) for d, ixp in ranked if d <= 100]
    nearby_250mi = [(d, ixp) for d, ixp in ranked if d <= 250]

    # Scoring tiers based on practical latency impact
    if nearest_dist < 25:
        score = 100  # essentially co-located with backbone
    elif nearest_dist < 50:
        score = 88
    elif nearest_dist < 100:
        score = 73
    elif nearest_dist < 200:
        score = 52
    elif nearest_dist < 400:
        score = 32
    else:
        score = 15   # > 400 miles — prohibitive for true edge DC

    # Redundancy bonus: multiple IXPs nearby means path diversity
    if len(nearby_100mi) >= 3:
        score = min(100, score + 10)
    elif len(nearby_100mi) >= 2:
        score = min(100, score + 5)

    redundancy_note = (
        f"{len(nearby_100mi)} IXP(s) within 100 mi, {len(nearby_250mi)} within 250 mi"
    )

    return CriterionResult(
        name="Proximity to Users & IoT",
        score=round(score, 1),
        weight=WEIGHT,
        weighted_contribution=round(score * WEIGHT, 2),
        description=(
            "Distance to major Internet Exchange Points — every 100 miles adds ~1 ms "
            "of latency, which erodes the core value proposition of an edge data center"
        ),
        details=(
            f"Nearest IXP: {nearest_ixp['name']} ({nearest_ixp['city']}) — "
            f"{nearest_dist:.0f} mi | {redundancy_note}"
        ),
        data_available=True,
    )
