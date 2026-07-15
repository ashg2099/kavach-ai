"""
LangChain tools for Kavach AI.
Real APIs: Open-Meteo (weather), data.gov.in (Agmarknet prices, groundwater).
"""
import os
import httpx
from langchain.tools import tool
import json, re, os

def get_coordinates(district: str, state: str) -> tuple:
    import httpx
    
    # Try different query formats
    queries = [
        district,
        f"{district}, India",
        f"{district}, {state}",
    ]
    
    for query in queries:
        try:
            resp = httpx.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": query, "count": 1, "language": "en", "countryCode": "IN"},
                timeout=10.0
            )
            data = resp.json()
            if data.get("results"):
                r = data["results"][0]
                print(f"Geocoded '{district}' via query '{query}': {r['latitude']}, {r['longitude']}")
                return (r["latitude"], r["longitude"])
        except Exception as e:
            print(f"Geocoding error for '{query}': {e}")
            continue
    
    print(f"Geocoding failed for '{district}, {state}' — using India center fallback")
    return (20.5937, 78.9629)


@tool
async def verify_weather_event(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> dict:
    """
    Fetch real historical weather data from Open-Meteo API.
    Compares current period rainfall against 5-year historical average
    to classify excess/deficient using IMD standard categories.
    """
    from datetime import datetime, timedelta

    async def fetch_rainfall(lat, lon, s_date, e_date):
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat, "longitude": lon,
            "start_date": s_date, "end_date": e_date,
            "daily": ["precipitation_sum", "temperature_2m_max", "temperature_2m_min"],
            "timezone": "Asia/Kolkata",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        rainfall = data.get("daily", {}).get("precipitation_sum", [])
        return [r for r in rainfall if r is not None], data

    # --- Current period ---
    current_rain, current_data = await fetch_rainfall(latitude, longitude, start_date, end_date)
    current_total = sum(current_rain)
    max_daily = max(current_rain, default=0)
    days = len(current_rain)

    # --- Historical average: same period over past 5 years ---
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    historical_totals = []

    for yr_offset in range(1, 6):
        try:
            hist_start = (start_dt.replace(year=start_dt.year - yr_offset)).strftime("%Y-%m-%d")
            hist_end = (end_dt.replace(year=end_dt.year - yr_offset)).strftime("%Y-%m-%d")
            hist_rain, _ = await fetch_rainfall(latitude, longitude, hist_start, hist_end)
            if hist_rain:
                historical_totals.append(sum(hist_rain))
        except Exception:
            continue

    historical_avg = sum(historical_totals) / len(historical_totals) if historical_totals else None

    # --- IMD classification ---
    # Large Excess: >60% above normal
    # Excess: 20–60% above normal
    # Normal: -19% to +19%
    # Deficient: -59% to -20% below normal
    # Large Deficient: <-60% below normal
    if historical_avg and historical_avg > 0:
        deviation_pct = ((current_total - historical_avg) / historical_avg) * 100
        if deviation_pct > 60:
            event_type = "Large Excess Rainfall"
            weather_confirmed = True
        elif deviation_pct > 20:
            event_type = "Excess Rainfall / Waterlogging"
            weather_confirmed = True
        elif deviation_pct < -60:
            event_type = "Large Deficient Rainfall / Severe Drought"
            weather_confirmed = True
        elif deviation_pct < -20:
            event_type = "Deficient Rainfall / Drought"
            weather_confirmed = True
        else:
            event_type = "Normal Rainfall"
            weather_confirmed = False
    else:
        # Fallback if historical fetch fails: use max daily spike
        deviation_pct = None
        if max_daily > 115.5:
            event_type = "Extremely Heavy Rainfall"
            weather_confirmed = True
        elif max_daily > 64.5:
            event_type = "Heavy Rainfall / Flash Flood"
            weather_confirmed = True
        else:
            event_type = "Normal Rainfall"
            weather_confirmed = False

    return {
        "total_rainfall_mm": round(current_total, 2),
        "max_single_day_mm": round(max_daily, 2),
        "days_analyzed": days,
        "historical_avg_mm": round(historical_avg, 2) if historical_avg else None,
        "deviation_from_normal_pct": round(deviation_pct, 1) if deviation_pct is not None else None,
        "event_type": event_type,
        "weather_event_confirmed": weather_confirmed,
        "imd_classification": "IMD standard: Excess >20%, Deficient <-20% of historical normal",
        "raw_daily": current_rain[:10],
    }


@tool
async def get_crop_prices(commodity: str, state: str) -> dict:
    """
    Fetch mandi prices from data.gov.in Agmarknet dataset.
    Falls back to reference MSP data if API unavailable.
    """
    api_key = os.getenv("DATA_GOV_API_KEY", "")
    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    params = {
        "api-key": api_key,
        "format": "json",
        "limit": 10,
        "filters[commodity]": commodity.title(),
        "filters[state]": state.title(),
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("records", [])
                if records:
                    prices = [float(r.get("modal_price", 0)) for r in records if r.get("modal_price")]
                    avg_price = sum(prices) / len(prices) if prices else 0
                    return {
                        "commodity": commodity,
                        "state": state,
                        "avg_modal_price_per_quintal": round(avg_price, 2),
                        "source": "Agmarknet / data.gov.in (live)",
                    }
    except Exception:
        pass

    REFERENCE_PRICES = {
        "rice": 2183, "wheat": 2275, "cotton": 6620,
        "soybean": 4600, "maize": 2090, "tur": 7000,
        "mustard": 5650, "gram": 5440, "groundnut": 6783,
        "onion": 1800, "sugarcane": 315,
    }
    price = REFERENCE_PRICES.get(commodity.lower(), 2500)
    return {
        "commodity": commodity,
        "state": state,
        "avg_modal_price_per_quintal": price,
        "source": "Reference MSP 2024-25 (live API fallback)",
    }


@tool
async def get_groundwater_status(district: str, state: str) -> dict:
    """
    Fetch groundwater level from CGWB / data.gov.in.
    Falls back to reference district data.
    """
    api_key = os.getenv("DATA_GOV_API_KEY", "")
    url = "https://api.data.gov.in/resource/8a9a9b8c-6678-4b79-8623-4f5b7b9c0c47"
    params = {
        "api-key": api_key,
        "format": "json",
        "limit": 5,
        "filters[district_name]": district.title(),
        "filters[state_name]": state.title(),
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("records", [])
                if records:
                    depths = [float(r.get("depth_to_water_level", 0)) for r in records if r.get("depth_to_water_level")]
                    avg_depth = sum(depths) / len(depths) if depths else 15.0
                    status = "critical" if avg_depth > 20 else "moderate" if avg_depth > 10 else "stable"
                    return {"district": district, "avg_depth_mbgl": round(avg_depth, 1), "status": status, "source": "CGWB live"}
    except Exception:
        pass

    GROUNDWATER_MAP = {
        "ludhiana": {"depth": 28.4, "status": "critical"},
        "amritsar": {"depth": 31.2, "status": "critical"},
        "patiala": {"depth": 25.8, "status": "critical"},
        "bathinda": {"depth": 22.1, "status": "critical"},
        "nagpur": {"depth": 8.5, "status": "moderate"},
        "amravati": {"depth": 11.2, "status": "moderate"},
        "guntur": {"depth": 12.4, "status": "moderate"},
        "vidisha": {"depth": 14.2, "status": "moderate"},
    }
    ref = GROUNDWATER_MAP.get(district.lower(), {"depth": 12.0, "status": "moderate"})
    return {"district": district, "avg_depth_mbgl": ref["depth"], "status": ref["status"], "source": "CGWB Reference Data"}

async def check_pmfby_coverage(crop: str, state: str, season: str = "Kharif") -> dict:
    """Check PMFBY coverage using LLM."""
    
    from langchain_groq import ChatGroq

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
    )

    prompt = f"""You are an expert on India's Pradhan Mantri Fasal Bima Yojana (PMFBY) crop insurance scheme.

Determine if the following crop is covered under PMFBY:
- Crop: {crop}
- State: {state}
- Season: {season}

Key facts:
- Rice/Paddy is covered in almost every Indian state for Kharif season
- Wheat is covered in North Indian states for Rabi season
- Cotton, Sugarcane, Groundnut are covered in their primary growing states
- Tamil Nadu covers Rice, Groundnut, Sugarcane, Banana, Maize
- If unsure, lean toward covered=true for staple crops (Rice, Wheat, Maize) in any Indian state

Respond ONLY with valid JSON, no extra text:
{{
  "covered": true or false,
  "reason": "one line explanation",
  "sum_insured_per_hectare": integer (40000 for rice, 75000 for cotton, 35000 for wheat, 60000 for sugarcane, 50000 for banana, 30000 for others)
}}"""

    response = llm.invoke(prompt)
    text = response.content.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        data = json.loads(match.group())
    else:
        data = {"covered": True, "reason": "Defaulting to covered", "sum_insured_per_hectare": 30000}

    return {
        "covered": data.get("covered", True),
        "crop": crop,
        "state": state,
        "season": season,
        "sum_insured_per_hectare": data.get("sum_insured_per_hectare", 30000) if data.get("covered") else 0,
        "insurance_company": "Agriculture Insurance Company of India (AIC)",
        "pmfby_portal": "https://pmfby.gov.in",
    }

@tool
def get_scheme_info(scheme_name: str) -> str:
    """Retrieve government agricultural scheme details."""
    SCHEMES = {
        "pmksy": """PMKSY — Drip & Sprinkler Irrigation Subsidy
- Benefit: 55% subsidy for general farmers, 90% for small/marginal farmers
- Application: pmksy.gov.in or state agriculture department
- Average benefit: ₹40,000-1,20,000 depending on land size
- Water saving: 40-50% compared to flood irrigation""",
        "pm kusum": """PM KUSUM — Solar Pump Scheme
- Benefit: 90% subsidy (Centre + State) on solar agricultural pumps
- Farmer pays only 10% of pump cost (~₹35,000 for 7.5 HP pump)
- Portal: mnre.gov.in/pm-kusum
- Eliminates electricity cost for irrigation permanently""",
        "pkvy": """PKVY — Organic Farming Scheme
- Benefit: ₹50,000/hectare over 3 years
- Eligibility: Groups of 50+ farmers, 50+ acres cluster
- Certification: Free PGS-India organic certification
- Market premium: 20-50% higher price for organic produce
- Portal: pgsindia-ncof.gov.in""",
    }
    key = scheme_name.lower()
    for k, v in SCHEMES.items():
        if k in key or key in k:
            return v
    return f"Scheme '{scheme_name}' not found. Check india.gov.in for details."