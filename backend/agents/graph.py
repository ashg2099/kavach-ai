"""
Kavach AI — 9-agent LangGraph pipeline.
Module 1 (FasalBima): Coverage → Weather → Claim → Document → Escalation
Module 2 (KrishiShift): Groundwater → Economics → Subsidies → Roadmap
"""
import os
from typing import Literal
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
from langgraph.graph import StateGraph, END

from .state import KavachState
from .tools import (
    verify_weather_event, get_crop_prices,
    get_groundwater_status, check_pmfby_coverage,
    get_scheme_info, get_coordinates,
)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2,
)


# MODULE 1 

async def agent_coverage_checker(state: KavachState) -> KavachState:
    state["current_agent"] = "Coverage Checker"
    state["agent_log"].append("🔍 Checking PMFBY coverage for your crop and region...")
    result = await check_pmfby_coverage(
        crop=state["crop"], state=state["state"], season="Kharif"
    )
    state["pmfby_covered"] = result["covered"]
    state["pmfby_coverage_details"] = (
        f"✅ {state['crop'].title()} is PMFBY covered in {state['state'].title()} — "
        f"Sum insured ₹{result['sum_insured_per_hectare']:,}/hectare."
        if result["covered"] else
        f"❌ {state['crop'].title()} is not in the notified crop list for {state['state'].title()} this season."
    )
    state["agent_log"].append(state["pmfby_coverage_details"])
    return state


async def agent_loss_verifier(state: KavachState) -> KavachState:
    state["current_agent"] = "Loss Verifier"
    state["agent_log"].append("🌦️ Fetching real historical weather data from Open-Meteo...")
    lat, lon = get_coordinates(state["district"], state["state"])
    state["latitude"] = lat
    state["longitude"] = lon
    try:
        sow = datetime.strptime(state["sowing_date"], "%Y-%m-%d")
    except Exception:
        sow = datetime(2024, 6, 15)
    end = sow + timedelta(days=120)
    end = min(end, datetime.now() - timedelta(days=1))
    weather = await verify_weather_event.ainvoke({
        "latitude": lat, "longitude": lon,
        "start_date": sow.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
    })
    state["rainfall_mm"] = weather["total_rainfall_mm"]
    state["weather_event_confirmed"] = weather["weather_event_confirmed"]
    state["weather_event_details"] = (
        f"🌧️ {state['district'].title()}: {weather['total_rainfall_mm']}mm total over "
        f"{weather['days_analyzed']} days. Event: {weather['event_type']}. "
        f"{'CONFIRMED for claim.' if weather['weather_event_confirmed'] else 'No extreme event in official records.'}"
    )
    state["agent_log"].append(state["weather_event_details"])
    return state


async def agent_claim_calculator(state: KavachState) -> KavachState:
    state["current_agent"] = "Claim Calculator"
    state["agent_log"].append("🧮 Computing your insurance entitlement...")
    SUM_INSURED = {
        "rice": 40000, "wheat": 35000, "cotton": 75000,
        "soybean": 30000, "maize": 28000, "tur": 32000,
        "groundnut": 35000, "bajra": 22000, "mustard": 28000,
    }
    per_ha = SUM_INSURED.get(state["crop"].lower(), 30000)
    hectares = state["land_size_acres"] * 0.4047
    loss_frac = min(state["loss_percentage"] / 100, 1.0)
    amount = per_ha * hectares * loss_frac
    state["claim_amount_inr"] = round(amount, 2)
    state["agent_log"].append(
        f"💰 Entitlement: ₹{amount:,.0f} "
        f"({state['loss_percentage']}% loss × ₹{per_ha:,}/ha × {hectares:.2f} ha)"
    )
    return state


async def agent_doc_drafter(state: KavachState) -> KavachState:
    state["current_agent"] = "Document Drafter"
    state["agent_log"].append("📝 Drafting your insurance claim letter...")
    prompt = f"""Draft a formal PMFBY crop insurance claim letter using this exact format and structure:

{state['farmer_name']}
{state['district'].title()}, {state['state'].title()}
[Date]

To,
The Branch Manager
[Insurance Company/Bank Name]
[Address]

Subject: Claim under Pradhan Mantri Fasal Bima Yojana (PMFBY) for {state['crop'].title()} Crop

Dear Sir/Madam,

I, {state['farmer_name']}, a farmer from {state['district'].title()}, {state['state'].title()}, am writing to submit a claim under PMFBY for my {state['crop'].title()} crop. I had sown on {state['land_size_acres']} acres on {state['sowing_date']}.

IMPORTANT: Use the VERIFIED weather event as the official basis — not the farmer's own description.
Verified event: {state['weather_event_details']}
Loss: {state['loss_percentage']}% | Claim amount: ₹{state['claim_amount_inr']:,.0f}

The letter body must include:
- The officially verified weather event and rainfall data as evidence
- Crop loss percentage and calculated claim amount
- Demand for settlement within the stipulated timelines per PMFBY guidelines (Section 16)N
- Required documents checklist (land records, sowing certificate, crop cutting report, weather data)
- Explicitly state: "In case of non-settlement of admissible claims within the stipulated timelines, I reserve the right to claim penal interest at the rate of 12% per annum as per Section 16 of the PMFBY Operational Guidelines."

End the letter with:
Yours faithfully,

{state['farmer_name']}
Signature: _____________________________
Date: __________________________________"""

    resp = llm.invoke([HumanMessage(content=prompt)])
    state["claim_document_text"] = resp.content
    STATE_LANGUAGE = {
        "maharashtra": "Marathi", "punjab": "Punjabi",
        "madhya pradesh": "Hindi", "rajasthan": "Hindi",
        "haryana": "Hindi", "uttar pradesh": "Hindi",
        "andhra pradesh": "Telugu", "telangana": "Telugu",
        "gujarat": "Gujarati", "karnataka": "Kannada",
        "tamil nadu": "Tamil", "west bengal": "Bengali",
    }
    
    local_lang = STATE_LANGUAGE.get(state["state"].lower(), "Hindi")
    state["claim_document_language"] = local_lang

    trans_prompt = f"""You are a professional translator specializing in formal legal and government documents.

Translate the following crop insurance claim letter to {local_lang}.

Rules:
- Keep all numbers, rupee amounts (₹), dates, and proper nouns exactly as-is — especially person names and place names must NOT be transliterated, keep them in English (e.g. "Ramesh" stays "Ramesh", "Thanjavur" stays "Thanjavur")
- "Dear Sir/Madam" → translate as "மதிப்பிற்குரிய ஐயா/அம்மா," in Tamil. For other languages use the culturally correct formal greeting used in official government letters
- "Subject:" → translate as "பொருள்:" in Tamil, "విషయం:" in Telugu, "विषय:" in Hindi/Marathi/Rajasthani, "વિષય:" in Gujarati, "ವಿಷಯ:" in Kannada, "বিষয়:" in Bengali, "ਵਿਸ਼ਾ:" in Punjabi
- The opening address line (e.g. "To, The Authorized Officer") should NOT use the word for "Sender" — translate it as the recipient address block
- Maintain formal, official letter tone throughout
- Preserve the letter structure and formatting
- Only translate, do not add or remove content

{state['claim_document_text']}"""
    trans_resp = llm.invoke([HumanMessage(content=trans_prompt)])
    state["claim_document_translated"] = trans_resp.content
    state["agent_log"].append("✅ Claim document drafted.")
    return state

async def agent_escalation(state: KavachState) -> KavachState:
    state["current_agent"] = "Escalation Agent"
    state["agent_log"].append("⚖️ Preparing legal rights and escalation guidance...")
    prompt = f"""You are an agricultural rights expert in India.

Farmer in {state['district'].title()}, {state['state'].title()}.
Crop: {state['crop'].title()} | Weather confirmed: {state['weather_event_confirmed']}
Claim: ₹{state['claim_amount_inr']:,.0f}

In under 200 words provide:
1. Key PMFBY farmer rights (60-day settlement, 12% interest on delay)
2. Escalation path: Bank → Insurance Company → District Grievance Cell → Ombudsman → CPGRAMS
3. Portal links: pmfby.gov.in and pgportal.gov.in
4. One PMFBY guideline they can quote if claim is rejected"""
    resp = llm.invoke([HumanMessage(content=prompt)])
    state["escalation_guidance"] = resp.content
    state["agent_log"].append("✅ Escalation guidance ready.")
    return state


# MODULE 2 

async def agent_root_cause_analyser(state: KavachState) -> KavachState:
    state["current_agent"] = "Root Cause Analyser"
    state["agent_log"].append("🔬 Analysing groundwater depletion and climate risk...")
    gw = await get_groundwater_status.ainvoke({
        "district": state["district"], "state": state["state"]
    })
    state["groundwater_status"] = gw["status"]
    state["groundwater_depth_mbgl"] = gw["avg_depth_mbgl"]
    risk = 30
    if gw["status"] == "critical": risk += 40
    elif gw["status"] == "moderate": risk += 20
    if state["rainfall_mm"] < 400: risk += 20
    elif state["rainfall_mm"] > 1200: risk += 10
    state["crop_risk_score"] = min(risk, 100)
    state["agent_log"].append(
        f"📊 Groundwater: {gw['avg_depth_mbgl']}m depth ({gw['status'].upper()}). "
        f"Crop vulnerability: {state['crop_risk_score']}/100."
    )
    return state


async def agent_transition_economics(state: KavachState) -> KavachState:
    state["current_agent"] = "Transition Economics Agent"
    state["agent_log"].append("📈 Comparing crop incomes using live Agmarknet prices...")

    # Use LLM to get region-appropriate alternatives
    alt_prompt = f"""You are an Indian agricultural expert.

A farmer in {state['district'].title()}, {state['state'].title()} currently grows {state['crop'].title()}.

List exactly 3 alternative crops that are:
1. Actually and commonly grown in {state['district'].title()}, {state['state'].title()}
2. Suitable as alternatives to {state['crop'].title()} given local soil and climate
3. Different from {state['crop'].title()}

Respond ONLY with valid JSON, no explanation:
{{"alternatives": ["crop1", "crop2", "crop3"]}}

Use lowercase crop names."""

    alt_resp = llm.invoke([HumanMessage(content=alt_prompt)])
    import json, re
    match = re.search(r'\{.*\}', alt_resp.content, re.DOTALL)
    if match:
        alternatives = json.loads(match.group()).get("alternatives", ["maize", "groundnut", "tur"])
    else:
        alternatives = ["maize", "groundnut", "tur"]

    YIELDS_PER_ACRE = {
        "rice": 25, "wheat": 30, "cotton": 8, "soybean": 12,
        "maize": 25, "tur": 8, "mustard": 10, "gram": 10,
        "sugarcane": 200, "groundnut": 12, "banana": 30,
        "onion": 80, "tomato": 120, "potato": 80,
        "green gram": 6, "black gram": 6, "turmeric": 25,
    }

    curr_price = await get_crop_prices.ainvoke({"commodity": state["crop"], "state": state["state"]})
    curr_yield = YIELDS_PER_ACRE.get(state["crop"].lower(), 20)
    current_income = curr_price["avg_modal_price_per_quintal"] * curr_yield * state["land_size_acres"] / 100

    alt_data = []
    for alt in alternatives[:3]:
        ap = await get_crop_prices.ainvoke({"commodity": alt, "state": state["state"]})
        alt_yield = YIELDS_PER_ACRE.get(alt.lower(), 15)
        alt_income = ap["avg_modal_price_per_quintal"] * alt_yield * state["land_size_acres"] / 100
        alt_data.append({
            "crop": alt,
            "est_income_per_acre": round(alt_income / state["land_size_acres"], 0),
            "water_req": "LOW" if alt in ["tur", "gram", "mustard", "green gram", "black gram"] else "MEDIUM"
        })

    income_dict = {state["crop"].title(): round(current_income / state["land_size_acres"], 0)}
    for a in alt_data:
        income_dict[a["crop"].title()] = a["est_income_per_acre"]

    state["income_comparison"] = income_dict
    state["alternative_crops"] = alternatives
    best = max(alt_data, key=lambda x: x["est_income_per_acre"])
    state["agent_log"].append(
        f"💹 {state['crop'].title()}: ₹{current_income:,.0f} total. "
        f"Best alternative: {best['crop'].title()} with {best['water_req']} water."
    )
    return state


async def agent_subsidy_hunter(state: KavachState) -> KavachState:
    state["current_agent"] = "Subsidy Hunter"
    state["agent_log"].append("🏆 Finding government schemes you qualify for...")
    subsidies = []
    pmksy = get_scheme_info.invoke({"scheme_name": "pmksy"})
    subsidies.append(f"PMKSY Drip Irrigation: 55-90% subsidy → apply at pmksy.gov.in")
    if state["groundwater_status"] in ["critical", "moderate"]:
        subsidies.append(f"PM KUSUM Solar Pump: 90% subsidy → apply at mnre.gov.in/pm-kusum")
    subsidies.append(f"PKVY Organic Farming: ₹50,000/hectare over 3 years → pgsindia-ncof.gov.in")
    subsidies.append(f"Kisan Credit Card: 4% interest crop loans up to ₹3 lakh → any nationalised bank")
    state["subsidies"] = subsidies
    state["agent_log"].append(f"💎 Found {len(subsidies)} applicable schemes.")
    return state


async def agent_transition_planner(state: KavachState) -> KavachState:
    state["current_agent"] = "Transition Planner"
    state["agent_log"].append("🗺️ Generating your 3-season transition roadmap...")
    subsidies_str = "\n".join(f"- {s}" for s in state["subsidies"])
    alts = list(state["income_comparison"].keys())
    best_alt = alts[1] if len(alts) > 1 else "Maize"

    prompt = f"""You are an agricultural expert for Indian smallholder farmers with deep knowledge of which crops are actually grown in each Indian state and district.

Farmer: {state['district'].title()}, {state['state'].title()}
Current crop: {state['crop'].title()} on {state['land_size_acres']} acres
Groundwater: {state['groundwater_status'].upper()} at {state['groundwater_depth_mbgl']}m
Crop risk score: {state['crop_risk_score']}/100
Best alternative crop: {best_alt}

Available subsidies:
{subsidies_str}

IMPORTANT: Only suggest crops that are actually and commonly grown in {state['district'].title()}, {state['state'].title()}. Use your knowledge of local agro-climatic conditions, soil type, and traditional farming practices of that specific district. Do NOT suggest crops from other regions.

Write a practical 3-season transition plan (under 280 words):
Season 1 (NOW): Risk reduction without losing this season's income
Season 2 (NEXT SEASON): Crop mix shift using locally appropriate crops + first subsidy to apply
Season 3 (TARGET): Full transition, income projection, water savings
Include: which local mandi or APMC to target, one risk measure per season.
Open with one motivating line for the farmer."""

    resp = llm.invoke([HumanMessage(content=prompt)])
    state["transition_plan"] = resp.content
    state["complete"] = True
    state["agent_log"].append("✅ Kavach AI analysis complete.")
    return state


# ROUTING 

def route_after_coverage(state: KavachState) -> Literal["loss_verifier", "escalation"]:
    return "loss_verifier" if state.get("pmfby_covered") else "escalation"


# BUILD GRAPH 

def build_kavach_graph():
    g = StateGraph(KavachState)
    g.add_node("coverage_checker", agent_coverage_checker)
    g.add_node("loss_verifier", agent_loss_verifier)
    g.add_node("claim_calculator", agent_claim_calculator)
    g.add_node("doc_drafter", agent_doc_drafter)
    g.add_node("escalation", agent_escalation)
    g.add_node("root_cause_analyser", agent_root_cause_analyser)
    g.add_node("transition_economics", agent_transition_economics)
    g.add_node("subsidy_hunter", agent_subsidy_hunter)
    g.add_node("transition_planner", agent_transition_planner)

    g.set_entry_point("coverage_checker")
    g.add_conditional_edges("coverage_checker", route_after_coverage,
                            {"loss_verifier": "loss_verifier", "escalation": "escalation"})
    g.add_edge("loss_verifier", "claim_calculator")
    g.add_edge("claim_calculator", "doc_drafter")
    g.add_edge("doc_drafter", "escalation")
    g.add_edge("escalation", "root_cause_analyser")
    g.add_edge("root_cause_analyser", "transition_economics")
    g.add_edge("transition_economics", "subsidy_hunter")
    g.add_edge("subsidy_hunter", "transition_planner")
    g.add_edge("transition_planner", END)
    return g.compile()


kavach_graph = build_kavach_graph()