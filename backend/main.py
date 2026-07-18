"""
Kavach AI — FastAPI Backend with SSE streaming.
"""
import os
import json
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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