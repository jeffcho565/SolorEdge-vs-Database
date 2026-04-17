from pydantic import BaseModel
from typing import Optional


class CriterionResult(BaseModel):
    name: str
    score: float          # 0–100: higher = better for edge data center
    weight: float         # fraction of total score (all weights sum to 1)
    weighted_contribution: float  # score * weight
    description: str      # what this criterion measures
    details: str          # specific findings from the data source
    data_available: bool  # whether live data was retrieved


class GeoLocation(BaseModel):
    lat: float
    lon: float
    formatted_address: str
    city: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    state_fips: Optional[str] = None
    county_fips: Optional[str] = None
    place_type: Optional[str] = None     # e.g. "building:house", "amenity:office"
    is_residential: bool = False         # True when Nominatim detects a home address


class EvaluationResult(BaseModel):
    address: str
    location: GeoLocation
    overall_score: float          # 0–100 data center feasibility
    solar_score: float            # 0–100 solar feasibility
    recommendation: str           # "data_center" | "solar"
    recommendation_confidence: str  # "strong" | "moderate" | "weak"
    criteria: list[CriterionResult]
    narrative: str
    key_strengths: list[str]
    key_weaknesses: list[str]
    data_sources_available: int
    data_sources_total: int
    address_warning: Optional[str] = None  # set when address looks residential
    flip_insight: str = ""                 # plain-English explanation of what flips the recommendation
    solar_policy: list[str] = []           # state-level solar laws and incentives
