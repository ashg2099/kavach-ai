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

# ── Conversation state (in-memory) ──────────────────────────────────────
conversations: dict = {}

STEPS = ["district", "state", "crop", "loss_percentage", "sowing_date", "land_size_acres", "loss_description"]

LANGUAGE_OPTIONS = {
    "1": "English", "2": "Hindi", "3": "Marathi",
    "4": "Tamil", "5": "Telugu", "6": "Kannada"
}

LANGUAGE_WELCOME = (
    "🌾 *Welcome to Kavach AI!*\n\n"
    "Choose your language / अपनी भाषा चुनें:\n\n"
    "1️⃣ English\n"
    "2️⃣ हिंदी (Hindi)\n"
    "3️⃣ मराठी (Marathi)\n"
    "4️⃣ தமிழ் (Tamil)\n"
    "5️⃣ తెలుగు (Telugu)\n"
    "6️⃣ ಕನ್ನಡ (Kannada)\n"
    "7️⃣ Other language\n\n"
    "Reply with number / नंबर भेजें"
)

QUESTIONS_BY_LANG = {
    "English": {
        "district":        "📍 Which *district* are you from?\n(e.g. Latur, Nagpur, Warangal)",
        "state":           "🗺️ Which *state*?\n(e.g. Maharashtra, Punjab, Telangana)",
        "crop":            "🌾 Which *crop* did you grow?\n(e.g. Rice, Cotton, Soybean)",
        "loss_percentage": "📉 What % of the crop was damaged?\n(just the number, e.g. 60)",
        "sowing_date":     "📅 When did you sow?\n(format: YYYY-MM-DD, e.g. 2024-06-15)",
        "land_size_acres": "🌱 How many *acres* of land?\n(e.g. 2.5)",
        "loss_description":"💬 Briefly describe what happened",
    },
    "Hindi": {
        "district":        "📍 आप किस *जिले* से हैं?\n(जैसे: लातूर, नागपुर, वारंगल)",
        "state":           "🗺️ आप किस *राज्य* से हैं?\n(जैसे: महाराष्ट्र, पंजाब, तेलंगाना)",
        "crop":            "🌾 आपने कौन सी *फसल* उगाई?\n(जैसे: चावल, कपास, सोयाबीन)",
        "loss_percentage": "📉 फसल का कितने *प्रतिशत* नुकसान हुआ?\n(सिर्फ नंबर, जैसे: 60)",
        "sowing_date":     "📅 आपने फसल कब बोई?\n(YYYY-MM-DD, जैसे: 2024-06-15)",
        "land_size_acres": "🌱 आपके पास कितने *एकड़* जमीन है?\n(जैसे: 2.5)",
        "loss_description":"💬 संक्षेप में बताएं क्या हुआ",
    },
    "Marathi": {
        "district":        "📍 तुम्ही कोणत्या *जिल्ह्यातून* आहात?\n(उदा: लातूर, नागपूर, वर्धा)",
        "state":           "🗺️ तुमचे *राज्य* कोणते?\n(उदा: महाराष्ट्र, पंजाब, तेलंगणा)",
        "crop":            "🌾 तुम्ही कोणते *पीक* घेतले?\n(उदा: भात, कापूस, सोयाबीन)",
        "loss_percentage": "📉 पिकाचे किती *टक्के* नुकसान झाले?\n(फक्त नंबर, उदा: 60)",
        "sowing_date":     "📅 तुम्ही पीक केव्हा पेरले?\n(YYYY-MM-DD, उदा: 2024-06-15)",
        "land_size_acres": "🌱 तुमच्याकडे किती *एकर* जमीन आहे?\n(उदा: 2.5)",
        "loss_description":"💬 थोडक्यात सांगा काय झाले",
    },
    "Tamil": {
        "district":        "📍 நீங்கள் எந்த *மாவட்டத்தை* சேர்ந்தவர்?\n(எ.கா: தஞ்சாவூர், கோயம்புத்தூர்)",
        "state":           "🗺️ உங்கள் *மாநிலம்* எது?\n(எ.கா: தமிழ்நாடு, மகாராஷ்டிரா)",
        "crop":            "🌾 நீங்கள் என்ன *பயிர்* விளைவித்தீர்கள்?\n(எ.கா: நெல், பருத்தி, சோளம்)",
        "loss_percentage": "📉 பயிரில் எத்தனை *சதவீதம்* சேதம்?\n(எண் மட்டும், எ.கா: 60)",
        "sowing_date":     "📅 நீங்கள் எப்போது விதைத்தீர்கள்?\n(YYYY-MM-DD, எ.கா: 2024-06-15)",
        "land_size_acres": "🌱 உங்களிடம் எத்தனை *ஏக்கர்* நிலம்?\n(எ.கா: 2.5)",
        "loss_description":"💬 என்ன நடந்தது என்று சுருக்கமாக சொல்லுங்கள்",
    },
    "Telugu": {
        "district":        "📍 మీరు ఏ *జిల్లా* నుండి వచ్చారు?\n(ఉదా: వరంగల్, నల్గొండ, కృష్ణా)",
        "state":           "🗺️ మీ *రాష్ట్రం* ఏది?\n(ఉదా: తెలంగాణ, ఆంధ్రప్రదేశ్, మహారాష్ట్ర)",
        "crop":            "🌾 మీరు ఏ *పంట* పండించారు?\n(ఉదా: వరి, పత్తి, సోయాబీన్)",
        "loss_percentage": "📉 పంటకు ఎంత *శాతం* నష్టం జరిగింది?\n(సంఖ్య మాత్రమే, ఉదా: 60)",
        "sowing_date":     "📅 మీరు ఎప్పుడు విత్తనాలు వేశారు?\n(YYYY-MM-DD, ఉదా: 2024-06-15)",
        "land_size_acres": "🌱 మీకు ఎన్ని *ఎకరాల* భూమి ఉంది?\n(ఉదా: 2.5)",
        "loss_description":"💬 ఏమి జరిగిందో క్లుప్తంగా వివరించండి",
    },
    "Kannada": {
        "district":        "📍 ನೀವು ಯಾವ *ಜಿಲ್ಲೆ*ಯಿಂದ ಬಂದಿದ್ದೀರಿ?\n(ಉದಾ: ಬೀದರ್, ಗುಲ್ಬರ್ಗ, ರಾಯಚೂರು)",
        "state":           "🗺️ ನಿಮ್ಮ *ರಾಜ್ಯ* ಯಾವುದು?\n(ಉದಾ: ಕರ್ನಾಟಕ, ಮಹಾರಾಷ್ಟ್ರ, ತೆಲಂಗಾಣ)",
        "crop":            "🌾 ನೀವು ಯಾವ *ಬೆಳೆ* ಬೆಳೆದಿದ್ದೀರಿ?\n(ಉದಾ: ಭತ್ತ, ಹತ್ತಿ, ಸೋಯಾಬೀನ್)",
        "loss_percentage": "📉 ಬೆಳೆಗೆ ಎಷ್ಟು *ಶೇಕಡಾ* ಹಾನಿ ಆಗಿದೆ?\n(ಸಂಖ್ಯೆ ಮಾತ್ರ, ಉದಾ: 60)",
        "sowing_date":     "📅 ನೀವು ಯಾವಾಗ ಬಿತ್ತನೆ ಮಾಡಿದಿರಿ?\n(YYYY-MM-DD, ಉದಾ: 2024-06-15)",
        "land_size_acres": "🌱 ನಿಮ್ಮ ಬಳಿ ಎಷ್ಟು *ಎಕರೆ* ಜಮೀನು ಇದೆ?\n(ಉದಾ: 2.5)",
        "loss_description":"💬 ಏನಾಯಿತು ಎಂದು ಸಂಕ್ಷಿಪ್ತವಾಗಿ ವಿವರಿಸಿ",
    },
}

PROCESSING_MSG = {
    "English": "⏳ Processing your claim... ~30 seconds 🙏",
    "Hindi":   "⏳ आपका दावा प्रोसेस हो रहा है... ~30 सेकंड 🙏",
    "Marathi": "⏳ तुमचा दावा प्रक्रिया होत आहे... ~30 सेकंद 🙏",
    "Tamil":   "⏳ உங்கள் கோரிக்கை செயலாக்கப்படுகிறது... ~30 வினாடிகள் 🙏",
    "Telugu":  "⏳ మీ దావా ప్రాసెస్ అవుతోంది... ~30 సెకన్లు 🙏",
    "Kannada": "⏳ ನಿಮ್ಮ ಕ್ಲೈಮ್ ಪ್ರಕ್ರಿಯೆಯಾಗುತ್ತಿದೆ... ~30 ಸೆಕೆಂಡ್‌ಗಳು 🙏",
}

RESET_MSG = {
    "English": "💬 Type *reset* to check another claim.",
    "Hindi":   "💬 दूसरा दावा जांचने के लिए *reset* टाइप करें।",
    "Marathi": "💬 दुसरा दावा तपासण्यासाठी *reset* टाइप करा.",
    "Tamil":   "💬 மற்றொரு கோரிக்கை சரிபார்க்க *reset* என தட்டச்சு செய்யுங்கள்.",
    "Telugu":  "💬 మరొక దావా తనిఖీ చేయడానికి *reset* టైప్ చేయండి.",
    "Kannada": "💬 ಮತ್ತೊಂದು ಕ್ಲೈಮ್ ಪರಿಶೀಲಿಸಲು *reset* ಟೈಪ್ ಮಾಡಿ.",
}


def parse_step_value(step: str, text: str):
    import re
    text = text.strip()
    if step == "loss_percentage":
        val = float(text.replace("%", "").strip())
        if not 1 <= val <= 100:
            raise ValueError("out of range")
        return val
    if step == "land_size_acres":
        val = float(text)
        if val <= 0:
            raise ValueError("must be positive")
        return val
    if step == "sowing_date":
        text = text.replace("/", "-")
        if re.match(r"^\d{2}-\d{2}-\d{4}$", text):
            d, m, y = text.split("-")
            text = f"{y}-{m}-{d}"
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", text):
            raise ValueError("invalid date format")
        return text
    if len(text) < 2:
        raise ValueError("too short")
    return text


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

        # Reset / greet
        if text.lower() in ("reset", "restart", "new", "start", "hi", "hello", "helo", "hey"):
            conversations.pop(from_number, None)
            conversations[from_number] = {"step": "language", "data": {}, "language": "English"}
            await send_wa_message(from_number, LANGUAGE_WELCOME)
            return JSONResponse({"status": "ok"})

        # New user
        if from_number not in conversations:
            conversations[from_number] = {"step": "language", "data": {}, "language": "English"}
            await send_wa_message(from_number, LANGUAGE_WELCOME)
            return JSONResponse({"status": "ok"})

        conv = conversations[from_number]
        step = conv["step"]
        lang = conv.get("language", "English")

        # Still processing
        if step == "processing":
            await send_wa_message(from_number, PROCESSING_MSG.get(lang, "⏳ Still working, please wait..."))
            return JSONResponse({"status": "ok"})

        # Language selection
        if step == "language":
            if text.strip() in LANGUAGE_OPTIONS:
                lang = LANGUAGE_OPTIONS[text.strip()]
                conv["language"] = lang
                conv["step"] = STEPS[0]
                await send_wa_message(from_number, f"✅ {lang}!\n\n{QUESTIONS_BY_LANG[lang][STEPS[0]]}")
            elif text.strip() == "7":
                conv["step"] = "custom_language"
                await send_wa_message(from_number, "Please type your language name:\n(e.g. Gujarati, Odia, Punjabi, Bengali)")
            else:
                await send_wa_message(from_number, LANGUAGE_WELCOME)
            return JSONResponse({"status": "ok"})

        # Custom language name entry
        if step == "custom_language":
            custom_lang = text.strip().title()
            conv["language"] = custom_lang
            conv["step"] = STEPS[0]
            first_q = await translate_with_groq(QUESTIONS_BY_LANG["English"][STEPS[0]], custom_lang)
            conv["translated_questions"] = {}
            conv["translated_questions"][STEPS[0]] = first_q
            await send_wa_message(from_number, f"✅ {custom_lang}!\n\n{first_q}")
            return JSONResponse({"status": "ok"})

        # Validate input
        try:
            parsed_value = parse_step_value(step, text)
        except Exception:
            error_hints = {
                "loss_percentage": {"English": "Send a number 1–100 (e.g. *60*)", "Hindi": "1–100 के बीच नंबर भेजें", "Marathi": "1–100 मधील नंबर पाठवा", "Tamil": "1–100 எண் அனுப்புங்கள்", "Telugu": "1–100 సంఖ్య పంపండి", "Kannada": "1–100 ಸಂಖ್ಯೆ ಕಳಿಸಿ"},
                "land_size_acres": {"English": "Send a number like *2* or *2.5*", "Hindi": "*2* या *2.5* जैसा नंबर भेजें", "Marathi": "*2* किंवा *2.5* पाठवा", "Tamil": "*2* அல்லது *2.5* அனுப்புங்கள்", "Telugu": "*2* లేదా *2.5* పంపండి", "Kannada": "*2* ಅಥವಾ *2.5* ಕಳಿಸಿ"},
                "sowing_date": {"English": "Use format *YYYY-MM-DD* (e.g. 2024-06-15)", "Hindi": "*YYYY-MM-DD* फॉर्मेट (जैसे: 2024-06-15)", "Marathi": "*YYYY-MM-DD* (उदा: 2024-06-15)", "Tamil": "*YYYY-MM-DD* (எ.கா: 2024-06-15)", "Telugu": "*YYYY-MM-DD* (ఉదా: 2024-06-15)", "Kannada": "*YYYY-MM-DD* (ಉದಾ: 2024-06-15)"},
            }
            hint = error_hints.get(step, {}).get(lang, "Please try again.")
            await send_wa_message(from_number, f"❌ {hint}")
            return JSONResponse({"status": "ok"})

        conv["data"][step] = parsed_value
        current_index = STEPS.index(step)

        if current_index < len(STEPS) - 1:
            next_step = STEPS[current_index + 1]
            conv["step"] = next_step
            lang = conv.get("language", "English")
            if lang in QUESTIONS_BY_LANG:
                next_q = QUESTIONS_BY_LANG[lang][next_step]
            else:
                # Custom language — translate on the fly
                cached = conv.get("translated_questions", {})
                if next_step not in cached:
                    cached[next_step] = await translate_with_groq(QUESTIONS_BY_LANG["English"][next_step], lang)
                    conv["translated_questions"] = cached
                next_q = cached[next_step]
            await send_wa_message(from_number, f"✅ Got it!\n\n{next_q}")
        else:
            # All data collected — run pipeline
            conv["step"] = "processing"
            d = conv["data"]
            farmer_data = {
                "farmer_name": "Farmer",
                "district": d["district"], "state": d["state"], "crop": d["crop"],
                "loss_percentage": float(d["loss_percentage"]),
                "sowing_date": d["sowing_date"],
                "loss_description": d["loss_description"],
                "land_size_acres": float(d["land_size_acres"]),
            }
            await send_wa_message(from_number, PROCESSING_MSG.get(lang, PROCESSING_MSG["English"]))
            result = await run_kavach(farmer_data)

            # Send summary
            await send_wa_message(from_number, format_reply(result))

            # Send full claim letter if claim is valid
            if result.get("weather_event_confirmed") and result.get("claim_amount_inr", 0) > 0:
                letter = result.get("claim_document_translated") or result.get("claim_document_text", "")
                if letter:
                    await send_long_message(from_number, f"📄 *Your Claim Letter*\n\n{letter}")

            await send_wa_message(from_number, RESET_MSG.get(lang, RESET_MSG["English"]))
            conversations.pop(from_number, None)

    except Exception as e:
        print(f"Webhook error: {e}")
    return JSONResponse({"status": "ok"})


async def send_long_message(to: str, text: str, chunk_size: int = 4000):
    if len(text) <= chunk_size:
        await send_wa_message(to, text)
        return
    parts = []
    while text:
        if len(text) <= chunk_size:
            parts.append(text); break
        split_at = text.rfind('\n', 0, chunk_size)
        if split_at == -1:
            split_at = chunk_size
        parts.append(text[:split_at])
        text = text[split_at:].lstrip('\n')
    for i, part in enumerate(parts):
        prefix = f"📄 *Claim Letter ({i+1}/{len(parts)})*\n\n" if len(parts) > 1 else ""
        await send_wa_message(to, f"{prefix}{part}")
        await asyncio.sleep(0.5)

# ── Helpers ──────────────────────────────────────────────────────────────
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
        
async def translate_with_groq(text: str, language: str) -> str:
    from groq import AsyncGroq
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    resp = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"Translate the following WhatsApp message to {language}. Keep emojis and *bold* formatting. Return only the translation, nothing else.\n\n{text}"
        }],
        max_tokens=200,
    )
    return resp.choices[0].message.content.strip()