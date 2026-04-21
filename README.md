# Solar Landscape Hackathon 2026

Welcome to the Solar Landscape Hackathon.

---

## Project Overview

### What problem does this solve?

Building owners are being approached by two competing parties: Solar Landscape (rooftop solar) and data center developers (edge data centers). They need a fast, data-driven way to evaluate which opportunity is the stronger fit for their specific property.

This tool answers: **"Is this building a better candidate for an edge data center or for rooftop solar?"**

### Why is it valuable?

Solar Landscape needs to make this case quickly and credibly to win leases. This tool:

- Produces a scored, evidence-backed recommendation in under 60 seconds
- Pulls from seven real public data sources — no opinion, just data
- Shows the building owner exactly *why* their roof is a better solar candidate
- Scales to any US commercial address with no manual configuration
- Explains in plain English what single criterion change would flip the recommendation

---

## Architecture

### High-Level Design

```
Browser (Single-Page App)
        │  POST /api/evaluate  { address }
        ▼
FastAPI Backend (src/app.py)
        │
        ├── Geocoding (Nominatim + Census Bureau)
        │       → lat/lon, county FIPS, state name
        │
        └── asyncio.gather() — seven criteria evaluated in parallel:
                │
                ├── Proximity to Users & IoT    IXP Haversine distance (20 major US campuses)
                ├── Network Connectivity         Census ACS B28002 broadband adoption %
                ├── Climate Resilience           USGS Earthquake API + wind/flood model
                ├── Renewable Energy Access      EIA grid mix 2023 (% renewable by state)
                ├── Roof & Building Suitability  OpenStreetMap Overpass API (building tags)
                ├── Cooling & Power Density      Open-Meteo historical temperature archive
                └── Market & Location Demand     Census ACS B01003 (county population)
                        │
                        ▼
                Weighted DC score + independent Solar score
                        │
                        ├── Recommendation (data_center | solar)
                        ├── Confidence (strong | moderate | weak)
                        ├── Flip Insight (plain-English: what single change flips the call)
                        └── State Solar Policy lookup (all 50 states + DC)
```

### Key Technologies

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, uvicorn, httpx (async HTTP) |
| Frontend | Single-page HTML, Tailwind CSS (CDN), Chart.js |
| Geocoding | Nominatim (OpenStreetMap), Census Bureau Geocoder |
| Broadband | US Census Bureau ACS 5-Year Estimates |
| Disaster Risk | USGS Earthquake Hazards API, Open-Meteo, geographic model |
| Building Type | OpenStreetMap Overpass API |
| IXP Proximity | Hardcoded PeeringDB / Equinix / CoreSite campus list |
| Climate | Open-Meteo Historical Archive API |
| Market Demand | US Census Bureau ACS 5-Year Estimates |
| Renewable Energy | EIA State Energy Data System (2023 grid mix) |
| Solar Policy | Static lookup — all 50 states + DC |

All data sources are **public and require no API keys**.

---

## Scoring Algorithm

Each criterion returns a score 0–100 (higher = better for edge data center):

| Criterion | Weight | Data Source |
|---|---|---|
| Proximity to Users & IoT | 22% | IXP Haversine distance |
| Network Connectivity | 20% | Census ACS broadband adoption rate |
| Climate Resilience | 18% | USGS seismic API + wind/flood model |
| Roof & Building Suitability | 15% | OpenStreetMap building tags |
| Renewable Energy Access | 13% | EIA grid mix 2023 (% renewable by state) |
| Cooling & Power Density | 7% | Open-Meteo average annual temperature |
| Market & Location Demand | 5% | Census ACS county population |

**DC Score** = weighted average of the seven criteria (weights re-normalised if a source is unavailable).

**Solar Score** = independent calculation weighting building type for solar suitability (large flat roofs score highest), solar irradiance proxy (warmer climate = more sun), and disaster risk (protects the long-lived asset).

**Recommendation** = whichever score is higher, with confidence based on the margin (strong ≥ 20 pts, moderate ≥ 10 pts, weak < 10 pts).

**Flip Insight** = algorithmic plain-English explanation of what single criterion improvement would flip the recommendation — or why no single change is sufficient.

---

## What Makes Our Approach Novel

**Internet Exchange Point (IXP) Proximity** is our most creative metric. Edge data centers exist to reduce latency — but latency depends not just on proximity to end users, but proximity to where the internet's backbone lives. Every 100 miles from a major IXP (like Equinix NY or DE-CIX Chicago) adds ~1 ms of round-trip latency. We score every address against a curated list of 20 major US IXP/carrier-neutral colocation campuses using the Haversine formula for geodesic distance. Most teams will use population as a demand proxy; we use backbone proximity as the actual latency-driver.

**Dual Scoring Model** shows both the data center score and the solar score on the same screen, derived from the same address and the same seven criteria. A building that scores poorly for a data center (retail space, large flat roof) immediately reveals itself as an excellent solar candidate — turning Solar Landscape's competitive disadvantage into the pitch itself.

**EIA Renewable Grid Mix as a Data Center Criterion** is an angle most teams won't consider: edge data centers increasingly require ESG compliance. A building in a state with high renewable energy penetration (e.g. Vermont, Iowa) is a more attractive DC site for operators who need to report Scope 2 emissions. We pull EIA 2023 state-level grid mix data and score it accordingly.

**State Solar Law Surfacing** provides a static lookup covering all 50 states and DC, surfacing net metering rules, ITC availability, state tax credits, RPS targets, and PACE financing where applicable. This gives the Solar Landscape sales team a ready-made policy argument for every address they evaluate.

**Flip Insight** is an algorithmic feature that computes, in plain English, exactly what single criterion improvement would flip the recommendation — or, if no single change is sufficient, explains why the recommendation is robust. This turns a black-box score into a negotiation tool: the sales rep can tell the building owner precisely what infrastructure investment would change the calculus.

---

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
python main.py
# or: uvicorn src.app:app --reload

# 3. Open the app
# Navigate to http://localhost:8000
```

No environment variables or API keys are required.

---

## Known Limitations / Future Improvements

### Data source substitutions made during the hackathon

- **FCC National Broadband Map**: The FCC NBM API requires Akamai bot-manager session authentication, making direct server-side calls impossible. We substituted Census ACS broadband adoption rate, which is a valid county-level proxy. A production system would use the FCC's registered bulk data download (FCC NBM) for fiber-level granularity at the census block level.

- **FEMA National Risk Index**: FEMA's NRI API is protected by WebSEAL and does not expose a public JSON endpoint. We built a composite disaster risk model using USGS earthquake data (live API), a state-level wind/hurricane model, and Open-Meteo precipitation data. FEMA NRI would give census-tract precision versus our state-level wind model.

### What we would improve with more time

- **NREL NSRDB for actual solar irradiance**: NREL's National Solar Radiation Database provides ground-truth GHI (Global Horizontal Irradiance) and DNI (Direct Normal Irradiance) data at 4 km resolution. Our current solar score uses average annual temperature as a crude proxy — NSRDB would replace this entirely.

- **OSM building footprint polygon area**: Larger roofs = more solar capacity and more rack space. OSM has building footprint polygons; we currently only inspect the building type tag. Computing actual roof area from the polygon geometry would improve both the solar suitability score and the DC scalability estimate.

- **FCC NBM bulk download for fiber granularity**: The FCC National Broadband Map bulk data download provides provider-level fiber availability at the address level. This would replace our county-level Census ACS broadband adoption rate with address-precise fiber/coax/DSL availability data.

- **FEMA NRI census-tract precision**: Our state-level wind and flood model is a reasonable approximation, but FEMA NRI provides composite risk scores at the census tract level, including social vulnerability and community resilience factors that affect DC siting decisions.

- **ML scoring calibration using Solar Landscape lease outcomes**: Once Solar Landscape has a corpus of addresses where leases were won or lost, the criterion weights could be calibrated using logistic regression or gradient boosting against actual outcomes — replacing our expert-assigned weights with data-driven ones.

- **International expansion**: The tool is currently US-only by design. Canada could be supported using NRCan solar resource data and Statistics Canada broadband surveys. EU expansion would use Eurostat broadband penetration and JRC PVGIS for solar irradiance.

- **Real-time EIA grid stress and outage frequency**: EIA provides grid reliability metrics (SAIDI/SAIFI) and real-time grid stress indicators via API. Adding outage frequency would improve the disaster risk and operational cost models significantly.

- **Satellite imagery via Google Solar API**: Google's Solar API provides roof segmentation, tilt, azimuth, and annual energy potential from satellite imagery. This would allow roof-level solar capacity estimation and replace our building-type heuristic with actual panel layout simulation.

### Edge cases not handled

- Non-US addresses (the tool is US-only by design)
- Addresses that resolve to rural areas with no OSM building data
- Multi-tenant buildings (the OSM tag reflects the dominant use, not all uses)
- Buildings under construction or recently demolished

---

## Team Workflow

### 1. Clone the Repository

```bash
git clone https://github.com/solarlandscape/<repo-name>.git
cd <repo-name>
```

### 2. Commit Early, Commit Often
```bash
git add .
git commit -m "Short descriptive message"
git push
```

### 3. Required Submission Structure

```
/
├── README.md
├── main.py
├── requirements.txt
├── src/
│   ├── app.py
│   ├── evaluator.py
│   ├── models.py
│   └── data_sources/
│       ├── broadband.py
│       ├── building_type.py
│       ├── climate.py
│       ├── disaster_risk.py
│       ├── geocoding.py
│       ├── ixp_proximity.py
│       ├── market_demand.py
│       ├── renewable_energy.py
│       └── solar_policy.py
├── static/
│   └── index.html
└── docs/
    └── demo.md
```

### 4. Submission Deadline

All code must be pushed before:

`Friday at 3:30PM EST`

### 5. Code Ownership

By participating, you acknowledge:
 - This repository is owned by Solar Landscape.
 - All submitted code remains in this repository after the event.
 - The organization may use, modify, or build upon submitted projects.
