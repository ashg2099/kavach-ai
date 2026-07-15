# 🛡️ Kavach AI — Crop Insurance Intelligence for Every Indian Farmer

> *"Kavach" means shield in Hindi. Because every farmer deserves one.*

🌐 **Live Demo:** https://kavach-ai-one.vercel.app/ 
⚙️ **Backend API:** https://kavach-ai-jyko.onrender.com

---

## The Problem — A Crisis Hidden in Plain Sight

Every year, millions of Indian farmers suffer crop losses due to drought, floods, and extreme weather. The government runs **PMFBY (Pradhan Mantri Fasal Bima Yojana)** — one of the world's largest crop insurance schemes — to protect them.

But here's the tragedy:

> **Most farmers never claim what they're owed.**

Not because they don't deserve it. But because:
- They don't know if their loss qualifies
- They can't navigate complex insurance paperwork in English
- They don't know their legal rights when claims are delayed
- They don't know who to approach or how to escalate

A farmer in Latur loses his entire soybean crop to drought. He paid his insurance premium. He qualifies for ₹29,000. But he walks away with nothing — because no one told him he could claim it.

**Kavach AI exists to change that.**

---

## The Solution — X → Y → Z

**X (The Situation):** A farmer just lost his crop. He has an insurance policy but has no idea what to do next.

**Y (The Complication):** The claim process requires weather verification, legal knowledge, document drafting, and knowledge of escalation channels — all in English, all bureaucratic.

**Z (The Resolution):** Kavach AI handles all of it in 30 seconds, in the farmer's own language.

---

## How It Works

A farmer enters 3 simple things:
1. **Who they are** — name, district, state
2. **What happened** — crop, sowing date, loss percentage
3. **Their insurance details** — sum insured

Kavach AI then runs **5 intelligent agents in sequence**:

🔍 Coverage Check → Are you eligible under PMFBY?
🌦️ Weather Verification → Did the event actually happen? (Real satellite data)
🧮 Claim Calculation → Exactly how much are you owed?
📝 Document Drafting → Ready-to-submit claim letter in your language
⚖️ Escalation Guidance → Your legal rights if the claim is denied

In 30 seconds, a farmer goes from confused to claim-ready.

---

## Real Intelligence, Not Fake Data

- We use **Open-Meteo Archive API** — free, real, satellite-backed historical rainfall data
- We use **Open-Meteo Geocoding API** — dynamically resolves any Indian district to precise GPS coordinates
- We compare against **5-year historical averages** using IMD rainfall classification standards
- If the weather event didn't happen, **we say so** — no false claims

**Example:**
- Latur, Maharashtra — 127.3mm over 30 days → Deficient Rainfall → Drought CONFIRMED ✅
- Kolhapur, Maharashtra — 275.8mm over 30 days → Normal for region → Not eligible ❌

The same AI that helps farmers also prevents fraud.

---

## Local Language Support

85% of Indian farmers are not comfortable in English. Kavach AI detects the farmer's state and automatically translates the claim letter into their regional language:

| State | Language |
|-------|----------|
| Tamil Nadu | Tamil |
| Maharashtra | Marathi |
| Punjab | Punjabi |
| West Bengal | Bengali |
| Gujarat | Gujarati |
| Karnataka | Kannada |
| Andhra Pradesh / Telangana | Telugu |
| Hindi belt (UP, MP, Rajasthan, Haryana) | Hindi |

The farmer can print the letter in English or their local language and walk into their bank the same day.

---

## Tech Stack

### Frontend
- **Next.js 14** — App Router, TypeScript
- **React** — SSE streaming for real-time agent progress
- Deployed on **Vercel**

### Backend
- **Python + FastAPI** — REST + Server-Sent Events (SSE)
- **LangGraph** — Multi-agent state machine orchestration
- **Groq API** — llama-3.3-70b-versatile (ultra-fast LLM inference)
- Deployed on **Render**

### Data & Intelligence
- **Open-Meteo Archive API** — Historical weather data (no API key needed)
- **Open-Meteo Geocoding API** — Dynamic district-to-coordinate resolution
- **IMD Classification Standards** — Rainfall event classification (Deficient / Excess / Normal)

### Agent Architecture

FarmerInput
│
├── agent_coverage_checker     → PMFBY eligibility by crop + state
├── agent_loss_verifier        → Real weather data + IMD classification
├── agent_claim_calculator     → Entitlement computation (loss% × sum insured × area)
├── agent_doc_drafter          → Formal claim letter + local language translation
└── agent_escalation           → Legal rights + escalation path (Section 16 PMFBY)

## Demo Scenarios

### Scenario 1 — Drought in Maharashtra
> *Ramesh Patil, Latur. 3 acres of Soybean. Sown June 15.*
> Weather confirmed: 127.3mm — Deficient Rainfall / Drought
> **Claim: ₹29,138 | Letter generated in Marathi**

### Scenario 2 — Drought in Tamil Nadu
> *Murugan S, Thanjavur. 2 acres of Rice. Sown June 1.*
> Weather confirmed: 65.0mm — Deficient Rainfall / Drought
> **Claim: ₹22,663 | Letter generated in Tamil**

### Scenario 3 — Claim Rejected (System Integrity)
> *Same farmer, same district. Normal rainfall period.*
> Weather: 51.6mm — Normal Rainfall. No extreme event.
> **Result: Not Eligible ❌ — Kavach AI prevents false claims**

## What's Next — KrishiShift

Kavach AI is one half of our vision. The other is **KrishiShift** — a crop transition planner that helps farmers answer:

> *"Now that I've lost this crop — what should I grow next season?"*

KrishiShift analyzes groundwater levels, soil suitability, market demand, and government subsidies to recommend the optimal crop transition — turning a crisis into a strategic pivot.

## Running Locally

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create .env with GROQ_API_KEY=your_key
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
# Create .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

## The Team

Built with ❤️ for Indian farmers at **The Talent Hack 2026** by Deutsche Telekom Digital Labs.

*Every ₹ a farmer doesn't claim is a failure of the system, not the farmer. Kavach AI fixes the system.*