"""
Kavach AI — FastAPI Backend with SSE streaming.
"""
import os
import json
import asyncio
from typing import AsyncGenerator
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()

from langfuse import Langfuse
langfuse = Langfuse()

from agents.graph import (
    agent_coverage_checker,
    agent_loss_verifier,
    agent_claim_calculator,
    agent_doc_drafter,
    agent_escalation,
    agent_root_cause_analyser,
    agent_transition_economics,
    agent_subsidy_hunter,
    agent_transition_planner,
)

import httpx

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = "kavach_webhook_secret"

app = FastAPI(title="Kavach AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FarmerInput(BaseModel):
    farmer_name: str
    district: str
    state: str
    crop: str
    sowing_date: str
    loss_description: str
    loss_percentage: float
    land_size_acres: float


class KrishiShiftInput(BaseModel):
    farmer_name: str
    district: str
    state: str
    crop: str
    land_size_acres: float


CLAIM_AGENTS = [
    agent_coverage_checker,
    agent_loss_verifier,
    agent_claim_calculator,
    agent_doc_drafter,
    agent_escalation,
]

async def stream_kavach_analysis(input_data: FarmerInput) -> AsyncGenerator[str, None]:
    state = {
        "farmer_name": input_data.farmer_name,
        "district": input_data.district,
        "state": input_data.state,
        "crop": input_data.crop,
        "sowing_date": input_data.sowing_date,
        "loss_description": input_data.loss_description,
        "loss_percentage": input_data.loss_percentage,
        "land_size_acres": input_data.land_size_acres,
        "latitude": 0.0, "longitude": 0.0,
        "pmfby_covered": False, "pmfby_coverage_details": "",
        "weather_event_confirmed": False, "weather_event_details": "",
        "rainfall_mm": 0.0, "claim_amount_inr": 0.0,
        "claim_document_text": "", "escalation_needed": False, "escalation_guidance": "",
        "claim_document_translated": "",
        "claim_document_language": "",
        "groundwater_status": "", "groundwater_depth_mbgl": 0.0,
        "crop_risk_score": 0, "alternative_crops": [],
        "income_comparison": {}, "subsidies": [], "transition_plan": "",
        "current_agent": "", "agent_log": [], "error": None, "complete": False,
    }
    langfuse.trace(
        name="kavach-claim-analysis",
        user_id=input_data.farmer_name,
        metadata={
            "district": input_data.district,
            "state": input_data.state,
            "crop": input_data.crop,
            "loss_percentage": input_data.loss_percentage,
        }
    )
    try:
        prev_len = 0
        for agent_fn in CLAIM_AGENTS:
            state = await agent_fn(state)
            for msg in state["agent_log"][prev_len:]:
                yield f"data: {json.dumps({'type': 'agent_update', 'message': msg})}\n\n"
            prev_len = len(state["agent_log"])
            await asyncio.sleep(0.05)

        result_data = {
            "pmfby_covered": state["pmfby_covered"],
            "pmfby_coverage_details": state["pmfby_coverage_details"],
            "weather_event_confirmed": state["weather_event_confirmed"],
            "weather_event_details": state["weather_event_details"],
            "rainfall_mm": state["rainfall_mm"],
            "claim_amount_inr": state["claim_amount_inr"],
            "claim_document_text": state["claim_document_text"],
            "escalation_guidance": state["escalation_guidance"],
            "agent_log": state["agent_log"],
            "claim_document_translated": state["claim_document_translated"],
            "claim_document_language": state["claim_document_language"],
        }
        yield f"data: {json.dumps({'type': 'result', 'data': result_data})}\n\n"
        langfuse.flush()
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

async def stream_krishishift(input_data: KrishiShiftInput) -> AsyncGenerator[str, None]:
    state = {
        "farmer_name": input_data.farmer_name,
        "district": input_data.district,
        "state": input_data.state,
        "crop": input_data.crop,
        "land_size_acres": input_data.land_size_acres,
        "sowing_date": "", "loss_description": "", "loss_percentage": 0,
        "latitude": 0.0, "longitude": 0.0,
        "pmfby_covered": False, "pmfby_coverage_details": "",
        "weather_event_confirmed": False, "weather_event_details": "",
        "rainfall_mm": 0.0, "claim_amount_inr": 0.0,
        "claim_document_text": "", "escalation_needed": False, "escalation_guidance": "",
        "groundwater_status": "", "groundwater_depth_mbgl": 0.0,
        "crop_risk_score": 0, "alternative_crops": [],
        "income_comparison": {}, "subsidies": [], "transition_plan": "",
        "current_agent": "", "agent_log": [], "error": None, "complete": False,
    }
    langfuse.trace(
        name="krishishift-transition-plan",
        user_id=input_data.farmer_name,
        metadata={
            "district": input_data.district,
            "state": input_data.state,
            "crop": input_data.crop,
        }
    )
    try:
        for agent_fn in [agent_root_cause_analyser, agent_transition_economics, agent_subsidy_hunter, agent_transition_planner]:
            state = await agent_fn(state)
            if state["agent_log"]:
                yield f"data: {json.dumps({'type': 'agent_update', 'message': state['agent_log'][-1]})}\n\n"
            await asyncio.sleep(0.05)

        result_data = {
            "groundwater_status": state["groundwater_status"],
            "groundwater_depth_mbgl": state["groundwater_depth_mbgl"],
            "crop_risk_score": state["crop_risk_score"],
            "income_comparison": state["income_comparison"],
            "subsidies": state["subsidies"],
            "transition_plan": state["transition_plan"],
        }
        yield f"data: {json.dumps({'type': 'result', 'data': result_data})}\n\n"
        langfuse.flush()
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@app.get("/")
def root():
    return {"name": "Kavach AI", "agents": 9, "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze")
async def analyze(input_data: FarmerInput):
    return StreamingResponse(
        stream_kavach_analysis(input_data),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@app.post("/krishishift")
async def krishishift_endpoint(input_data: KrishiShiftInput):
    return StreamingResponse(
        stream_krishishift(input_data),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
    
# ── Webhook verification (GET) ──────────────────────────────────────────
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(params.get("hub.challenge"))
    return JSONResponse({"error": "Forbidden"}, status_code=403)

# ── Receive WhatsApp message (POST) ─────────────────────────────────────
@app.post("/webhook")
async def receive_whatsapp(request: Request):
    data = await request.json()
    try:
        value = data["entry"][0]["changes"][0]["value"]
        if "messages" not in value:
            return JSONResponse({"status": "ok"})

        msg = value["messages"][0]
        from_number = msg["from"]

        if msg["type"] != "text":
            await send_wa_message(from_number, "Please send text only 🙏")
            return JSONResponse({"status": "ok"})

        text = msg["text"]["body"].strip()
        parsed = parse_claim_text(text)

        if not parsed:
            await send_wa_message(from_number,
                "🌾 *Welcome to Kavach AI*\n\nSend your claim in this format:\n"
                "*District, State, Crop, Loss%*\n\nExample:\n_Latur, Maharashtra, Rice, 60_"
            )
            return JSONResponse({"status": "ok"})

        await send_wa_message(from_number,
            f"⏳ Processing claim for *{parsed['district']}, {parsed['state']}*...\n(~30 seconds)"
        )

        result = await run_kavach(parsed)
        reply = format_reply(result)
        await send_wa_message(from_number, reply)

    except Exception as e:
        print(f"Webhook error: {e}")

    return JSONResponse({"status": "ok"})

# ── Helpers ──────────────────────────────────────────────────────────────
def parse_claim_text(text: str):
    parts = [p.strip() for p in text.split(",")]
    if len(parts) < 4:
        return None
    try:
        return {
            "farmer_name": parts[4].strip() if len(parts) > 4 else "Farmer",
            "district": parts[0],
            "state": parts[1],
            "crop": parts[2],
            "loss_percentage": float(parts[3].replace("%", "")),
            "sowing_date": parts[5].strip() if len(parts) > 5 else "2024-06-15",
            "loss_description": parts[6].strip() if len(parts) > 6 else "Crop loss reported via WhatsApp",
            "land_size_acres": float(parts[7].strip()) if len(parts) > 7 else 2.0,
        }
    except:
        return None

async def run_kavach(parsed: dict):
    state = {
        **parsed,
        "latitude": 0.0, "longitude": 0.0,
        "pmfby_covered": False, "pmfby_coverage_details": "",
        "weather_event_confirmed": False, "weather_event_details": "",
        "rainfall_mm": 0.0, "claim_amount_inr": 0.0,
        "claim_document_text": "", "claim_document_translated": "",
        "claim_document_language": "",
        "escalation_needed": False, "escalation_guidance": "",
        "groundwater_status": "", "groundwater_depth_mbgl": 0.0,
        "crop_risk_score": 0, "alternative_crops": [],
        "income_comparison": {}, "subsidies": [], "transition_plan": "",
        "current_agent": "", "agent_log": [], "error": None, "complete": False,
    }
    for agent_fn in CLAIM_AGENTS:
        state = await agent_fn(state)
    return state

def format_reply(result: dict) -> str:
    confirmed = result.get("weather_event_confirmed", False)
    rainfall = result.get("rainfall_mm", 0)
    amount = result.get("claim_amount_inr", 0)
    details = result.get("weather_event_details", "")[:150]
    emoji = "✅" if confirmed else "❌"
    return (
        f"🌾 *Kavach AI Result*\n\n"
        f"{emoji} *Weather Confirmed:* {'Yes' if confirmed else 'No'}\n"
        f"🌧 *Rainfall:* {rainfall:.1f} mm\n"
        f"💰 *Claim Amount:* ₹{amount:,.0f}\n"
        f"📊 *Details:* {details}\n\n"
        f"_Full report: kavach-ai.vercel.app_"
    )

async def send_wa_message(to: str, text: str):
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }, headers={
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        })
        print(f"WhatsApp send to {to}: {resp.status_code} — {resp.text}")