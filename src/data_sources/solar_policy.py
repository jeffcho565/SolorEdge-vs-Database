"""
State-level solar laws and incentives lookup.

Returns a list of concise policy bullets for the given US state name,
covering net metering, financial incentives, tax exemptions, and RPS mandates
that directly affect Solar Landscape's rooftop solar programme.
"""

_POLICIES: dict[str, list[str]] = {
    "Alabama": [
        "Net metering capped at 5 kW residential; no commercial mandate — limited export value",
        "No state income tax credit or SREC market for solar",
        "No property or sales tax exemption for solar equipment",
    ],
    "Alaska": [
        "Net metering available through select co-ops; no statewide mandate",
        "Alaska Energy Authority Renewable Energy Fund: project grants available",
        "No statewide sales tax; high install costs offset by utility rate (~23¢/kWh)",
    ],
    "Arizona": [
        "Net metering at retail rate required for all investor-owned utilities",
        "Property tax: 100% of solar added value excluded from assessment",
        "Sales tax (TPT) exemption on residential solar equipment",
        "Renewable Energy Standard: 15% by 2025 — active procurement environment",
    ],
    "Arkansas": [
        "Net metering at avoided-cost rate (below retail); 300 kW system cap",
        "Property tax exemption for solar installations (Act 827 of 2015)",
        "Sales tax exemption on solar energy equipment (Ark. Code § 26-52-447)",
    ],
    "California": [
        "NEM 3.0 (2023): export credits ~75% lower than NEM 2.0 — self-consumption focus",
        "100% clean electricity mandate by 2045 (SB 100) — strong long-term market",
        "Property tax exclusion for new solar (Revenue & Taxation Code § 73)",
        "No state sales/use tax on solar energy systems",
        "SGIP rebates for battery storage paired with rooftop solar",
    ],
    "Colorado": [
        "Net metering required; 120% of annual consumption cap for residential",
        "Property tax: solar added value excluded from residential assessment",
        "Sales tax exemption on residential solar (C.R.S. § 39-26-724)",
        "100% clean electricity goal by 2040 (HB 19-1261) — active RFP pipeline",
    ],
    "Connecticut": [
        "Virtual net metering + ZREC (Zero-Emission REC) program for commercial solar",
        "Residential Solar Investment Program (RSIP): per-watt rebates available",
        "Property tax: 100% of solar added value excluded for 15 years",
        "Sales tax exemption on solar equipment (CGS § 12-412(114))",
        "RPS: 48% renewable by 2030 — strong SREC demand",
    ],
    "Delaware": [
        "Net metering at full retail rate; 25 kW residential cap",
        "Active SREC market — additional monthly revenue per MWh generated",
        "Green Energy Program: commercial solar rebates up to $100,000",
        "RPS: 40% by 2035 with 10% solar carve-out",
    ],
    "Florida": [
        "Net metering at full retail rate required statewide (§ 366.91)",
        "Property tax exemption: 100% of solar added value excluded",
        "Sales tax exemption on solar equipment (Fla. Stat. § 212.08(7)(hh))",
        "Solar Rights Act: HOAs cannot prohibit solar (§ 163.04) — reduces install friction",
    ],
    "Georgia": [
        "No statewide net metering mandate; Georgia Power voluntary metering only",
        "No property tax or sales tax exemption for solar statewide",
        "Solar easement rights protected (O.C.G.A. § 44-9-20)",
        "Georgia Power Advanced Solar Initiative: utility procurement via competitive RFP",
    ],
    "Hawaii": [
        "Smart Export: exports credited at avoided-cost rate (~8–11¢/kWh); self-consumption key",
        "High retail rates (~37¢/kWh) make rooftop solar highly profitable",
        "100% renewable mandate by 2045 (HRS § 269-92) — strongest mandate in US",
        "Property tax exemptions vary by county; Green Infrastructure Loan Program available",
    ],
    "Idaho": [
        "Net metering at retail rate; 25 kW residential cap via Idaho Power / Rocky Mountain Power",
        "No statewide property tax exemption; some county-level exemptions exist",
        "No state income tax credit for solar installations",
    ],
    "Illinois": [
        "Illinois Shines (Adjustable Block Program): 15-year SREC contracts — major incentive",
        "Net metering at retail rate for utilities with 100,000+ customers",
        "Property tax: solar added value exempt from assessment (35 ILCS 200/10-5)",
        "RPS: 50% by 2040 with solar carve-out — active procurement market",
    ],
    "Indiana": [
        "Net metering transitioned to 'distributed generation' tariff — credits below retail since 2022",
        "Property tax deduction: up to $6,000 or 50% of system cost (lesser of two)",
        "No statewide sales tax exemption on solar equipment",
    ],
    "Iowa": [
        "Net metering required; no system size cap",
        "State solar tax credit: 50% of federal ITC (up to $5,000 residential / $20,000 commercial)",
        "Sales tax exemption on solar equipment (Iowa Code § 423.3(90))",
        "Property tax: 5-year assessment freeze for solar installations",
    ],
    "Kansas": [
        "No statewide net metering mandate; some utilities offer voluntary net metering",
        "Property tax: 100% of renewable energy system value excluded from assessment",
        "No state income tax credit or sales tax exemption for solar",
    ],
    "Kentucky": [
        "Net metering available; 30 kW residential cap",
        "TVA Green Power Providers: ~3.5¢/kWh for export in TVA territory",
        "No state income tax credit, property tax exemption, or sales tax exemption for solar",
    ],
    "Louisiana": [
        "Net metering at retail rate; 25 kW residential cap",
        "Property tax exemption for solar (La. R.S. 47:1706)",
        "Sales tax exemption on solar equipment (La. R.S. 47:305.41)",
    ],
    "Maine": [
        "Net Energy Billing at retail rate; strong community solar programme",
        "RPS: 80% by 2030, 100% by 2050 — active procurement pipeline",
        "Property tax exemption for solar installations",
        "Maine PACE financing available for commercial solar projects",
    ],
    "Maryland": [
        "Net metering at full retail rate; 2 MW system cap",
        "Active SREC market: SRECs sellable for additional revenue",
        "Property tax credit: up to $5,000 for residential solar",
        "Sales tax exemption on solar equipment",
        "RPS: 50% by 2030 with 14.5% solar carve-out",
    ],
    "Massachusetts": [
        "SMART program: 10-year fixed incentive payments per kWh generated",
        "Net metering at retail rate; strong community solar market",
        "Property tax: 20-year exemption on solar added value",
        "Sales tax exemption on residential solar (M.G.L. c. 64H § 6(dd))",
        "RPS: 35% by 2030 with Class I solar carve-out",
    ],
    "Michigan": [
        "Distributed Generation programme: credits at avoided cost (below retail)",
        "Property tax exemption for commercial solar (MCL § 211.9i)",
        "Sales tax exemption on solar energy systems",
        "60% clean energy by 2035 (PA 235) — growing procurement market",
    ],
    "Minnesota": [
        "Net metering at retail rate; 40 kW residential / 1 MW commercial cap",
        "Active community solar garden programme — large subscriber base",
        "Property tax: solar exempt from personal and real property tax",
        "Sales tax exemption on solar equipment (Minn. Stat. § 297A.67 subd. 29)",
        "100% carbon-free electricity by 2040 (SF 4)",
    ],
    "Mississippi": [
        "Net metering at retail rate for utilities with 25,000+ customers",
        "No state income tax credit, property tax exemption, or sales tax exemption",
    ],
    "Missouri": [
        "Net metering required for investor-owned utilities; 100 kW system cap",
        "Solar easement rights protected (Mo. Rev. Stat. § 442.012)",
        "No statewide property tax or sales tax exemption for solar",
    ],
    "Montana": [
        "Net metering at retail rate; 50 kW residential/commercial cap",
        "Property tax: 100% of solar added value excluded (MCA § 15-6-224)",
        "Montana has no general sales tax — no sales tax burden on equipment",
    ],
    "Nebraska": [
        "Net metering via LES, OPPD, and most public power districts",
        "Property tax exemption for solar under LB 436",
        "Sales tax exemption for commercial solar equipment",
        "Dollar and Energy Saving Loans programme for solar financing",
    ],
    "Nevada": [
        "Net metering restored at retail rate; strong residential/commercial market",
        "Nevada Solar Access Law: HOAs cannot prohibit solar (NRS § 111.239)",
        "Sales tax exemption on solar energy systems (NRS § 374.357)",
        "Commercial property tax abatement: 55% reduction for solar installations",
        "RPS: 50% by 2030, 100% carbon-free by 2050",
    ],
    "New Hampshire": [
        "Net metering at retail rate; 1 MW system cap",
        "Property tax: solar added value excluded for 5 years",
        "No general sales tax (NH has no sales tax) — no equipment tax burden",
        "RPS: 25.2% by 2025 with thermal carve-out",
    ],
    "New Jersey": [
        "Transition RECs (TRECs): quarterly state incentive payments per kWh",
        "Net metering at retail rate; strong community solar programme",
        "Sales tax: 100% exemption on solar equipment (N.J.S.A. 54:32B-8.55)",
        "Property tax: 100% exemption on solar added value (N.J.S.A. 54:4-3.113a)",
        "RPS: 50% by 2030 with 3.956 GW solar carve-out — one of strongest US markets",
    ],
    "New Mexico": [
        "Net metering at retail rate; 80 MW statewide cap (largely unused)",
        "State income tax credit: 10% of system cost up to $9,000",
        "Property tax and sales tax exemptions for solar systems",
        "Energy Transition Act: 50% renewables by 2030, 100% by 2045",
    ],
    "New York": [
        "NY-Sun Incentive Programme: per-watt rebates for residential and commercial",
        "Net metering at retail rate; remote net metering available",
        "Property tax: 15-year exemption on solar added value (RPTL § 487)",
        "Sales tax exemption on residential solar equipment",
        "Clean Energy Standard: 70% renewables by 2030, 100% zero-emission by 2040",
    ],
    "North Carolina": [
        "Net metering at retail rate; 1 MW system cap",
        "Strong commercial solar procurement by Duke Energy and Dominion",
        "Sales tax exemption on commercial solar equipment",
        "REPS: 12.5% by 2021 (met); no stronger mandate yet",
    ],
    "North Dakota": [
        "Net metering available; 100 kW cap",
        "Property tax: 5-year exemption on renewable energy additions",
        "Sales tax exemption for solar equipment",
    ],
    "Ohio": [
        "Net metering at retail rate; 120% of annual consumption cap",
        "Property tax exemption for solar (ORC § 5709.53)",
        "Sales tax exemption on solar equipment (ORC § 5739.02(B)(32))",
        "Note: HB 6 weakened RPS and removed solar carve-out in 2019",
    ],
    "Oklahoma": [
        "Net metering available but credits typically below retail rate",
        "No property tax exemption statewide for solar",
        "Sales tax exemption for manufacturing-use solar equipment only",
    ],
    "Oregon": [
        "Net metering at retail rate; 25 kW residential / 2 MW commercial cap",
        "Oregon Solar + Storage Rebate: up to $5,000 residential, $30,000 commercial",
        "Property tax: residential solar exempt from value-add assessment",
        "No general sales tax (Oregon has no sales tax)",
        "RPS: 50% by 2040, 100% by 2040 for large utilities",
    ],
    "Pennsylvania": [
        "Net metering at retail rate; 50 kW residential cap",
        "Active SREC market (PJM zone): SRECs tradeable for added revenue",
        "Sales tax exemption on residential solar equipment (72 P.S. § 7204(60))",
        "AEPS: 18% by 2021 with 0.5% solar carve-out",
    ],
    "Rhode Island": [
        "Distributed Generation tariff: retail-rate credits; robust community solar",
        "REG programme: 15-year fixed-price contracts for solar projects",
        "Property tax: 100% of solar added value excluded for 10 years",
        "Sales tax exemption on solar equipment",
        "RPS: 100% renewable by 2033 — fastest mandate in New England",
    ],
    "South Carolina": [
        "Net metering at retail rate; 20 kW residential / 1 MW commercial cap",
        "DERP programme: additional incentive payments per kWh",
        "Sales tax exemption on solar equipment",
    ],
    "South Dakota": [
        "Net metering available; 100 kW cap",
        "No state income tax (SD has no income tax)",
        "Property tax and sales tax exemptions for solar systems",
    ],
    "Tennessee": [
        "TVA controls ~60% of territory: TVA Green Power Providers pays ~3.5¢/kWh export",
        "Non-TVA utilities offer standard net metering",
        "No statewide property tax exemption or sales tax exemption for solar",
    ],
    "Texas": [
        "No statewide net metering mandate; ERCOT utilities offer buy-back at avoided cost",
        "Property tax: 100% of solar added value excluded (Texas Tax Code § 11.27)",
        "Sales tax exemption on solar energy devices (§ 151.355)",
        "Solar Rights Act: HOAs cannot ban solar (Tex. Prop. Code § 202.010)",
    ],
    "Utah": [
        "Net metering transitioning to 'Export Tariff'; credits below retail by 2033",
        "State income tax credit: 25% of cost up to $2,000 residential",
        "Property tax exemption for residential solar (Utah Code § 59-2-301)",
        "No sales tax on solar energy equipment",
    ],
    "Vermont": [
        "Net metering at retail rate; no system size cap",
        "Standard Offer: 10-year fixed-price contracts for small solar (<5 MW)",
        "Property tax: solar exempt from municipal property tax",
        "No general sales tax on solar in Vermont",
        "RPS: 75% by 2032 — one of most aggressive mandates in the US",
    ],
    "Virginia": [
        "Net metering at full retail rate; 20 kW residential cap",
        "Clean Economy Act: 100% carbon-free by 2045 (Dominion) / 2050 (APCo)",
        "Property tax: localities may exempt solar from real property assessment",
        "Solar Freedom Act (2020): removed local permit barriers for rooftop solar",
    ],
    "Washington": [
        "Net metering at retail rate; 100 kW system cap",
        "State sales tax exemption on solar (RCW 82.08.962) — significant cost saving",
        "Property tax: solar excluded from assessed value",
        "100% clean electricity by 2045 (Clean Energy Transformation Act)",
    ],
    "West Virginia": [
        "Net metering available; 25 kW residential cap",
        "No statewide property tax or sales tax exemption for solar",
        "Primarily coal grid; limited policy development for solar",
    ],
    "Wisconsin": [
        "Net metering: credits at average retail rate; 20 kW residential cap",
        "Focus on Energy programme: cash-back rewards for solar installations",
        "Property tax: renewables on commercial property exempt from tax",
        "No state sales tax exemption for solar equipment",
    ],
    "Wyoming": [
        "Net metering through Rocky Mountain Power and Black Hills Energy",
        "No state income tax (Wyoming has no income tax)",
        "Property tax: renewable energy systems excluded from assessment",
        "No mandatory RPS; limited solar-specific policy",
    ],
    "District of Columbia": [
        "Net metering at retail rate; premium DC SREC market",
        "Solar for All: 100% of programme benefits targeted at low-income households",
        "Property tax and sales tax exemptions for solar",
        "RPS: 100% renewable by 2032 with 10% solar carve-out",
    ],
}

_FEDERAL = "Federal ITC: 30% tax credit on total installed system cost (through 2032 — then steps down)"
_DEFAULT = [
    "Net metering policies vary by utility; confirm export credit rate before install",
    _FEDERAL,
]


def get_solar_policy(state: str | None) -> list[str]:
    """
    Return solar policy bullet points for the given full US state name
    (as returned by Nominatim geocoding, e.g. 'California', 'New Jersey').
    Falls back to generic federal guidance for unknown states.
    """
    if not state:
        return _DEFAULT
    policies = _POLICIES.get(state)
    if not policies:
        return _DEFAULT
    return policies + [_FEDERAL]
