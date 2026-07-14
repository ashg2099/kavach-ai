from typing import TypedDict, List, Optional


class KavachState(TypedDict):
    # Farmer Input
    farmer_name: str
    district: str
    state: str
    crop: str
    sowing_date: str
    loss_description: str
    loss_percentage: float
    land_size_acres: float

    # Geo
    latitude: float
    longitude: float

    # Module 1: Claim Intelligence
    pmfby_covered: bool
    pmfby_coverage_details: str
    weather_event_confirmed: bool
    weather_event_details: str
    rainfall_mm: float
    claim_amount_inr: float
    claim_document_text: str
    claim_document_translated: str
    claim_document_language: str
    escalation_needed: bool
    escalation_guidance: str

    # Module 2: KrishiShift
    groundwater_status: str
    groundwater_depth_mbgl: float
    crop_risk_score: int
    alternative_crops: List[str]
    income_comparison: dict
    subsidies: List[dict]
    transition_plan: str

    # Meta
    current_agent: str
    agent_log: List[str]
    error: Optional[str]
    complete: bool