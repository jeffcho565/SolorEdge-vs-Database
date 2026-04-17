"""
Geocoding: convert a free-text address to lat/lon and Census FIPS codes.

Primary:  US Census Bureau Geocoder (geographies endpoint)
          — free, no key, no rate limit, returns lat/lon + FIPS in one call
Fallback: Nominatim (OpenStreetMap) if Census can't resolve the address
          — free, no key, but rate-limited to 1 req/sec
"""

import asyncio
import time
import httpx
from src.models import GeoLocation

CENSUS_GEO_URL  = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
NOMINATIM_URL   = "https://nominatim.openstreetmap.org/search"
_HEADERS = {"User-Agent": "SolarLandscapeHackathon/1.0 (hackathon@solarlandscape.com)"}

# In-memory cache: normalised address string → GeoLocation
_CACHE: dict[str, GeoLocation] = {}
# Throttle Nominatim (fallback only) to ≤1 req/sec
_last_nominatim_call: float = 0.0

# OSM building types that unambiguously indicate a residential structure
_RESIDENTIAL_BUILDING_TYPES = {
    "residential", "apartments", "dormitory", "flat",
    "detached", "terrace", "semidetached_house", "bungalow",
    "cabin", "static_caravan", "houseboat",
}
_COMMERCIAL_ADDRESS_KEYS = {"amenity", "office", "shop", "tourism", "leisure"}

# Terms in a query or matched address that signal a non-residential property
_BUSINESS_KEYWORDS = {
    "suite", "ste", "floor", "fl", "bldg", "building", "unit",
    "dept", "department", "office", "ofc", "corp", "corporation",
    "inc", "llc", "ltd", "plaza", "tower", "center", "centre",
}


async def _geocode_census(client: httpx.AsyncClient, address: str) -> GeoLocation | None:
    """
    Try the Census Bureau geographies geocoder.
    Returns a GeoLocation (with FIPS already populated) or None if not found.
    One HTTP call gets lat/lon + state/county FIPS — no rate limit.
    """
    try:
        resp = await client.get(
            CENSUS_GEO_URL,
            params={
                "address": address,
                "benchmark": "Public_AR_Current",
                "vintage": "Current_Current",
                "format": "json",
            },
            headers=_HEADERS,
        )
        resp.raise_for_status()
        matches = resp.json().get("result", {}).get("addressMatches", [])
        if not matches:
            return None

        m = matches[0]
        coords = m["coordinates"]
        lon = float(coords["x"])
        lat = float(coords["y"])
        components = m.get("addressComponents", {})
        geos = m.get("geographies", {})
        counties = geos.get("Counties", [])
        states   = geos.get("States", [])

        state_name = states[0].get("NAME", "") if states else components.get("state", "")
        county_name = counties[0].get("NAME", "") if counties else ""
        state_fips  = counties[0].get("STATE", "")  if counties else ""
        county_fips = counties[0].get("COUNTY", "") if counties else ""

        # Heuristic: a numbered street address without business keywords
        # is very likely residential.  The Census geocoder doesn't tag
        # building type, but the vast majority of street-number addresses
        # in the US are homes.
        matched = m.get("matchedAddress", address)
        combined = f"{address} {matched}".lower()
        has_business = any(kw in combined for kw in _BUSINESS_KEYWORDS)
        is_residential = bool(components.get("fromAddress")) and not has_business

        return GeoLocation(
            lat=lat,
            lon=lon,
            formatted_address=matched,
            city=components.get("city", ""),
            state=state_name,
            county=county_name,
            state_fips=state_fips,
            county_fips=county_fips,
            place_type="address",
            is_residential=is_residential,
        )
    except Exception:
        return None


async def _geocode_nominatim(client: httpx.AsyncClient, address: str) -> GeoLocation:
    """
    Fallback geocoder using Nominatim. Throttled + retried on 429.
    Also does a Census coordinate lookup to populate FIPS codes.
    """
    global _last_nominatim_call

    gap = time.monotonic() - _last_nominatim_call
    if gap < 1.1:
        await asyncio.sleep(1.1 - gap)

    data = None
    for attempt in range(3):
        _last_nominatim_call = time.monotonic()
        resp = await client.get(
            NOMINATIM_URL,
            params={
                "q": address,
                "format": "json",
                "addressdetails": 1,
                "limit": 1,
                "countrycodes": "us",
            },
            headers=_HEADERS,
        )
        if resp.status_code == 429:
            await asyncio.sleep(2 ** attempt)   # 1s → 2s → 4s
            continue
        resp.raise_for_status()
        data = resp.json()
        break

    if not data:
        raise ValueError(f"Address not found: {address!r}")

    hit  = data[0]
    addr = hit.get("address", {})
    lat  = float(hit["lat"])
    lon  = float(hit["lon"])

    osm_class = hit.get("class", "")
    osm_type  = hit.get("type", "")
    place_type = f"{osm_class}:{osm_type}" if osm_type else osm_class

    is_residential = False
    if osm_class == "building" and osm_type in _RESIDENTIAL_BUILDING_TYPES:
        is_residential = True
    elif osm_class in ("building", "place") and osm_type == "house":
        has_business = any(k in addr for k in _COMMERCIAL_ADDRESS_KEYS)
        if not has_business and not hit.get("name"):
            is_residential = True

    location = GeoLocation(
        lat=lat,
        lon=lon,
        formatted_address=hit.get("display_name", address),
        city=addr.get("city") or addr.get("town") or addr.get("village"),
        state=addr.get("state"),
        county=addr.get("county"),
        place_type=place_type,
        is_residential=is_residential,
    )

    # Best-effort FIPS enrichment via Census coordinate lookup
    try:
        fips_resp = await client.get(
            "https://geocoding.geo.census.gov/geocoder/geographies/coordinates",
            params={
                "x": lon, "y": lat,
                "benchmark": "Public_AR_Current",
                "vintage": "Current_Current",
                "format": "json",
            },
            headers=_HEADERS,
        )
        counties = (
            fips_resp.json().get("result", {})
            .get("geographies", {})
            .get("Counties", [])
        )
        if counties:
            location.state_fips  = counties[0].get("STATE", "")
            location.county_fips = counties[0].get("COUNTY", "")
    except Exception:
        pass

    return location


async def geocode_address(address: str) -> GeoLocation:
    """Geocode an address. Uses Census geocoder first (no rate limit),
    falls back to Nominatim only if Census can't resolve it."""
    cache_key = address.strip().lower()
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    async with httpx.AsyncClient(timeout=12.0) as client:
        location = await _geocode_census(client, address)
        if location is None:
            # Census couldn't find it — try Nominatim as fallback
            location = await _geocode_nominatim(client, address)

    _CACHE[cache_key] = location
    return location
