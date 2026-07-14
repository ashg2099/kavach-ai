"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

interface StreamResult {
  pmfby_covered: boolean;
  pmfby_coverage_details: string;
  weather_event_confirmed: boolean;
  weather_event_details: string;
  rainfall_mm: number;
  claim_amount_inr: number;
  claim_document_text: string;
  claim_document_translated: string;
  claim_document_language: string;
  escalation_guidance: string;
  groundwater_status: string;
  groundwater_depth_mbgl: number;
  crop_risk_score: number;
  income_comparison: Record<string, number>;
  subsidies: any[];
  transition_plan: string;
  agent_log: string[];
}

type Phase = "form" | "streaming" | "results";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
const STATES = ["Maharashtra","Punjab","Madhya Pradesh","Rajasthan","Haryana","Andhra Pradesh","Telangana","Gujarat","Karnataka","Tamil Nadu","West Bengal","Uttar Pradesh"];
const CROPS = ["Rice","Wheat","Cotton","Soybean","Maize","Tur","Groundnut","Bajra","Mustard","Gram","Sugarcane","Onion","Tomato"];

const friendlyMsg = (msg: string) => {
  if (!msg) return "";
  if (/coverage/i.test(msg)) return "Checking if your crop is covered under PMFBY...";
  if (/weather|rainfall/i.test(msg)) return "Pulling official weather records for your district...";
  if (/calculat|claim amount/i.test(msg)) return "Calculating the claim amount you are owed...";
  if (/document|draft|letter/i.test(msg)) return "Writing your official claim letter...";
  if (/escalation|rights|legal/i.test(msg)) return "Looking up your legal rights under PMFBY...";
  if (/groundwater|root cause/i.test(msg)) return "Checking groundwater levels in your district...";
  if (/transition|price|income/i.test(msg)) return "Comparing crop prices across your region...";
  if (/subsidy|scheme/i.test(msg)) return "Finding government schemes you qualify for...";
  if (/planner|plan|roadmap/i.test(msg)) return "Building your 3-season farming roadmap...";
  return msg.replace(/[✅📝🌧️⚠️🔍📊🌱💰🗺️⏳]/g, "").trim();
};

export default function AnalyzePage() {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("form");
  const [agentMessages, setAgentMessages] = useState<string[]>([]);
  const [result, setResult] = useState<StreamResult | null>(null);
  const [error, setError] = useState("");
  const [lossPercent, setLossPercent] = useState(50);
  const [showTranslated, setShowTranslated] = useState(false);
  const [form, setForm] = useState({
    farmer_name: "", district: "", state: "", crop: "",
    sowing_date: "", loss_description: "", land_size_acres: 2,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPhase("streaming");
    setAgentMessages([]);
    setError("");
    try {
      const resp = await fetch(`${BACKEND_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, loss_percentage: lossPercent }),
      });
      if (!resp.ok) throw new Error("Could not connect to server");
      const reader = resp.body!.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const lines = decoder.decode(value).split("\n");
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === "agent_update" && data.message)
              setAgentMessages(prev => [...prev, data.message]);
            else if (data.type === "result") { setResult(data.data); setPhase("results"); }
            else if (data.type === "error") { setError(data.message); setPhase("form"); }
          } catch {}
        }
      }
    } catch (err: any) {
      setError(err.message || "Connection failed. Is the backend running?");
      setPhase("form");
    }
  };

  const inputStyle: React.CSSProperties = {
    width: "100%", padding: "12px 16px", borderRadius: "8px",
    border: "1.5px solid #e5e7eb", fontSize: "15px", outline: "none",
    background: "white", color: "#1a1a1a", boxSizing: "border-box",
    fontFamily: "-apple-system, system-ui, sans-serif",
  };

  const nav = (
    <nav style={{
      position: "fixed", top: 0, left: 0, right: 0, zIndex: 50,
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "16px 60px", background: "rgba(255,255,255,0.97)",
      backdropFilter: "blur(10px)", borderBottom: "1px solid #e5e7eb",
    }}>
      <button onClick={() => router.push("/")} style={{
        display: "flex", alignItems: "center", gap: "8px", background: "none",
        border: "none", cursor: "pointer", color: "#4b5563", fontSize: "15px", fontWeight: 600,
      }}>
        <ArrowLeft size={18} /> Back to Home
      </button>
      <div style={{ display: "flex", gap: "4px" }}>
        <span style={{ fontSize: "20px", fontWeight: 900, color: "#15803d" }}>Kavach</span>
        <span style={{ fontSize: "20px", fontWeight: 900, color: "#d97706" }}>AI</span>
      </div>
    </nav>
  );

  /* ── FORM ─────────────────────────── */
  if (phase === "form") {
    return (
      <main style={{ background: "#fafaf5", minHeight: "100vh", paddingTop: "80px", fontFamily: "-apple-system, system-ui, sans-serif" }}>
        {nav}
        <div style={{ padding: "60px" }}>
          <p style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "3px", textTransform: "uppercase", color: "#d97706", marginBottom: "12px" }}>
            Free · 2 minutes · No documents needed
          </p>
          <h1 style={{ fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 900, color: "#1a1a1a", marginBottom: "8px" }}>
            Tell us what happened to your crop
          </h1>
          <p style={{ fontSize: "17px", color: "#6b7280", marginBottom: "40px" }}>
            We'll verify the weather, check your coverage, and tell you exactly how much you can claim.
          </p>
          {error && (
            <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "12px", padding: "16px 20px", marginBottom: "24px", color: "#dc2626", fontSize: "15px" }}>
              ⚠️ {error}
            </div>
          )}
          <form onSubmit={handleSubmit}>
            <div style={{ background: "white", borderRadius: "16px", padding: "32px", marginBottom: "20px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
              <p style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "2px", textTransform: "uppercase", color: "#d97706", marginBottom: "24px" }}>Your Details</p>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>Your Full Name</label>
                  <input style={inputStyle} placeholder="e.g. Ramesh Kumar" value={form.farmer_name} onChange={e => setForm(p => ({ ...p, farmer_name: e.target.value }))} required />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>Your District</label>
                  <input style={inputStyle} placeholder="e.g. Nagpur" value={form.district} onChange={e => setForm(p => ({ ...p, district: e.target.value }))} required />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>Your State</label>
                  <select style={inputStyle} value={form.state} onChange={e => setForm(p => ({ ...p, state: e.target.value }))} required>
                    <option value="">Select your state...</option>
                    {STATES.map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>Crop You Grow</label>
                  <select style={inputStyle} value={form.crop} onChange={e => setForm(p => ({ ...p, crop: e.target.value }))} required>
                    <option value="">Select crop...</option>
                    {CROPS.map(c => <option key={c}>{c}</option>)}
                  </select>
                </div>
              </div>
            </div>

            <div style={{ background: "white", borderRadius: "16px", padding: "32px", marginBottom: "32px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
              <p style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "2px", textTransform: "uppercase", color: "#d97706", marginBottom: "24px" }}>What Happened</p>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginBottom: "20px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>When did you sow the crop?</label>
                  <input type="date" style={inputStyle} value={form.sowing_date} onChange={e => setForm(p => ({ ...p, sowing_date: e.target.value }))} required />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>How much land? (acres)</label>
                  <input type="number" min="0.1" step="0.1" style={inputStyle} value={form.land_size_acres} onChange={e => setForm(p => ({ ...p, land_size_acres: parseFloat(e.target.value) }))} required />
                </div>
              </div>
              <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>
                  How much of the crop was damaged? <span style={{ color: "#d97706", fontWeight: 900 }}>{lossPercent}%</span>
                </label>
                <input type="range" min={10} max={100} step={5} value={lossPercent} onChange={e => setLossPercent(parseInt(e.target.value))} style={{ width: "100%", accentColor: "#15803d" }} />
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#9ca3af", marginTop: "4px" }}>
                  <span>10% — small loss</span><span>50% — half lost</span><span>100% — total loss</span>
                </div>
              </div>
              <div>
                <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>Describe what happened in your own words</label>
                <textarea style={{ ...inputStyle, resize: "vertical" }} rows={4}
                  placeholder="e.g. Three weeks of continuous rain in July flooded the fields. The soybean crop was completely waterlogged and destroyed."
                  value={form.loss_description} onChange={e => setForm(p => ({ ...p, loss_description: e.target.value }))} required />
              </div>
            </div>

            <button type="submit" style={{
              width: "100%", padding: "18px", borderRadius: "12px", border: "none",
              background: "#15803d", color: "white", fontSize: "18px", fontWeight: 800,
              cursor: "pointer", boxShadow: "0 4px 20px rgba(21,128,61,0.3)",
            }}>
              Check My Claim →
            </button>
            <p style={{ textAlign: "center", color: "#9ca3af", fontSize: "13px", marginTop: "10px" }}>
              Free · Takes about 60 seconds · No documents needed to start
            </p>
          </form>
        </div>
      </main>
    );
  }

  /* ── STREAMING ────────────────────── */
  if (phase === "streaming") {
    return (
      <main style={{ background: "#fafaf5", minHeight: "100vh", paddingTop: "80px", fontFamily: "-apple-system, system-ui, sans-serif", display: "flex", alignItems: "center" }}>
        {nav}
        <div style={{ padding: "60px", maxWidth: "600px", margin: "0 auto", width: "100%", textAlign: "center" }}>
          <div style={{ width: "72px", height: "72px", borderRadius: "50%", background: "#dcfce7", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 24px", fontSize: "32px" }}>
            🌾
          </div>
          <h2 style={{ fontSize: "28px", fontWeight: 900, color: "#1a1a1a", marginBottom: "8px" }}>
            We're checking your situation...
          </h2>
          <p style={{ color: "#6b7280", marginBottom: "36px", fontSize: "16px" }}>
            Please don't close this page. This takes about 60 seconds.
          </p>
          <div style={{ background: "white", borderRadius: "16px", padding: "24px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)", textAlign: "left" }}>
            {agentMessages.length === 0
              ? <p style={{ color: "#9ca3af", fontSize: "15px" }}>Starting up...</p>
              : agentMessages.map((msg, i) => (
                <div key={i} style={{ display: "flex", gap: "12px", alignItems: "flex-start", padding: "10px 0", borderBottom: i < agentMessages.length - 1 ? "1px solid #f3f4f6" : "none" }}>
                  <span style={{ fontSize: "16px", flexShrink: 0 }}>{i === agentMessages.length - 1 ? "⏳" : "✅"}</span>
                  <span style={{ fontSize: "15px", color: i === agentMessages.length - 1 ? "#1a1a1a" : "#9ca3af", fontWeight: i === agentMessages.length - 1 ? 600 : 400 }}>
                    {friendlyMsg(msg)}
                  </span>
                </div>
              ))
            }
          </div>
          <div style={{ marginTop: "20px", background: "#e5e7eb", borderRadius: "100px", height: "6px" }}>
            <div style={{
              height: "6px", borderRadius: "100px", background: "#15803d",
              width: `${Math.min((agentMessages.length / 5) * 100, 95)}%`,
              transition: "width 0.5s ease",
            }} />
          </div>
          <p style={{ fontSize: "13px", color: "#9ca3af", marginTop: "8px" }}>Step {Math.min(agentMessages.length, 5)} of 5</p>
        </div>
      </main>
    );
  }

  /* ── RESULTS ──────────────────────── */
  if (!result) return null;

  return (
    <main style={{ background: "#fafaf5", minHeight: "100vh", paddingTop: "80px", fontFamily: "-apple-system, system-ui, sans-serif" }}>
      {nav}
      <div style={{ padding: "60px" }}>

        {/* HERO */}
        <div style={{
          background: result.pmfby_covered && result.weather_event_confirmed ? "#f0fdf4" : "#fef9f0",
          border: `2px solid ${result.pmfby_covered && result.weather_event_confirmed ? "#86efac" : "#fcd34d"}`,
          borderRadius: "20px", padding: "40px", marginBottom: "28px",
          display: "flex", justifyContent: "space-between", alignItems: "center", gap: "32px",
        }}>
          <div>
            <div style={{ fontSize: "40px", marginBottom: "12px" }}>
              {result.pmfby_covered && result.weather_event_confirmed ? "✅" : "⚠️"}
            </div>
            <h1 style={{ fontSize: "clamp(24px, 3vw, 36px)", fontWeight: 900, color: "#1a1a1a", marginBottom: "10px" }}>
              {result.pmfby_covered && result.weather_event_confirmed ? "Good news — your claim is valid!" : "Your situation has been assessed"}
            </h1>
            <p style={{ fontSize: "16px", color: "#4b5563", lineHeight: 1.6 }}>{result.pmfby_coverage_details}</p>
          </div>
          {result.claim_amount_inr > 0 && (
            <div style={{ background: "white", borderRadius: "16px", padding: "28px 36px", boxShadow: "0 4px 20px rgba(0,0,0,0.08)", textAlign: "center", flexShrink: 0 }}>
              <p style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "2px", textTransform: "uppercase", color: "#9ca3af", marginBottom: "8px" }}>You may receive</p>
              <p style={{ fontSize: "44px", fontWeight: 900, color: "#15803d", lineHeight: 1 }}>₹{result.claim_amount_inr.toLocaleString("en-IN")}</p>
              <p style={{ fontSize: "13px", color: "#9ca3af", marginTop: "4px" }}>estimated amount</p>
            </div>
          )}
        </div>

        {/* WEATHER + RIGHTS */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>
          <div style={{ background: "white", borderRadius: "16px", padding: "28px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
              <span style={{ fontSize: "22px" }}>🌧️</span>
              <h3 style={{ fontSize: "17px", fontWeight: 800, color: "#1a1a1a" }}>Weather Check</h3>
              {result.weather_event_confirmed && (
                <span style={{ background: "#dcfce7", color: "#15803d", fontSize: "11px", fontWeight: 700, padding: "3px 10px", borderRadius: "100px" }}>VERIFIED</span>
              )}
            </div>
            <p style={{ fontSize: "15px", color: "#4b5563", lineHeight: 1.7, marginBottom: "12px" }}>{result.weather_event_details}</p>
            {result.rainfall_mm > 0 && (
              <div style={{ background: "#f0f9ff", borderRadius: "8px", padding: "10px 14px" }}>
                <span style={{ fontSize: "14px", fontWeight: 600, color: "#0369a1" }}>💧 {result.rainfall_mm} mm rainfall recorded</span>
              </div>
            )}
          </div>
          <div style={{ background: "white", borderRadius: "16px", padding: "28px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
              <span style={{ fontSize: "22px" }}>⚖️</span>
              <h3 style={{ fontSize: "17px", fontWeight: 800, color: "#1a1a1a" }}>Your Rights</h3>
            </div>
            {(() => {
                const parts = (result.escalation_guidance || "").split(/\*\s+/);
                const intro = parts[0].trim();
                const bullets = parts.slice(1).filter(b => b.trim());
                return (
                    <>
                    {intro && (
                        <p style={{ fontSize: "14px", color: "#4b5563", lineHeight: 1.7, marginBottom: "12px" }}>
                        {intro}
                        </p>
                    )}
                    {bullets.map((b, i) => (
                        <div key={i} style={{ display: "flex", gap: "8px", alignItems: "flex-start", marginBottom: "8px" }}>
                        <span style={{ color: "#15803d", fontWeight: 900, flexShrink: 0, fontSize: "16px", lineHeight: 1.4 }}>•</span>
                        <span style={{ fontSize: "14px", color: "#4b5563", lineHeight: 1.6 }}>{b.trim()}</span>
                        </div>
                    ))}
                    </>
                );
                })()}
          </div>
        </div>

        {/* CLAIM LETTER */}
        {result.claim_document_text && (
        <div style={{ background: "white", borderRadius: "16px", padding: "32px", marginBottom: "24px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span style={{ fontSize: "22px" }}>📄</span>
                <h3 style={{ fontSize: "18px", fontWeight: 800, color: "#1a1a1a" }}>Your Claim Letter — Ready to Submit</h3>
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
                <button
                onClick={() => setShowTranslated(false)}
                style={{
                    padding: "8px 16px", borderRadius: "8px", fontSize: "13px", fontWeight: 700, cursor: "pointer",
                    background: !showTranslated ? "#15803d" : "white",
                    color: !showTranslated ? "white" : "#374151",
                    border: `1.5px solid ${!showTranslated ? "#15803d" : "#e5e7eb"}`,
                }}
                >
                English
                </button>
                <button
                onClick={() => setShowTranslated(true)}
                style={{
                    padding: "8px 16px", borderRadius: "8px", fontSize: "13px", fontWeight: 700, cursor: "pointer",
                    background: showTranslated ? "#15803d" : "white",
                    color: showTranslated ? "white" : "#374151",
                    border: `1.5px solid ${showTranslated ? "#15803d" : "#e5e7eb"}`,
                }}
                >
                {result.claim_document_language || "Local Language"}
                </button>
                <button onClick={() => window.print()} style={{ padding: "8px 16px", borderRadius: "8px", border: "1.5px solid #15803d", background: "white", color: "#15803d", fontWeight: 700, fontSize: "13px", cursor: "pointer" }}>
                🖨️ Print
                </button>
            </div>
            </div>
            <div style={{ background: "#fafaf5", borderRadius: "12px", padding: "24px", fontFamily: "Georgia, serif", fontSize: "14px", lineHeight: 1.9, color: "#374151", whiteSpace: "pre-wrap", border: "1px solid #e5e7eb" }}>
            {showTranslated ? result.claim_document_translated : result.claim_document_text}
            </div>
        </div>
        )}

        {/* KRISHISHIFT TEASER */}
        <div style={{
          background: "linear-gradient(135deg, #f0fdf4 0%, #fef9f0 100%)",
          border: "2px solid #bbf7d0", borderRadius: "16px", padding: "32px",
          marginBottom: "24px", display: "flex", alignItems: "center",
          justifyContent: "space-between", gap: "32px",
        }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "10px" }}>
              <span style={{ fontSize: "28px" }}>🌱</span>
              <h3 style={{ fontSize: "20px", fontWeight: 900, color: "#1a1a1a" }}>
                Don't lose money next season too
              </h3>
            </div>
            <p style={{ fontSize: "15px", color: "#4b5563", lineHeight: 1.7, maxWidth: "480px" }}>
              KrishiShift checks groundwater levels, finds government schemes, and builds a personalised 3-season crop plan so you can earn more and lose less.
            </p>
          </div>
          <button
            onClick={() => router.push("/krishishift")}
            style={{
              flexShrink: 0, padding: "16px 28px", borderRadius: "12px", border: "none",
              background: "#15803d", color: "white", fontSize: "16px", fontWeight: 800,
              cursor: "pointer", whiteSpace: "nowrap",
              boxShadow: "0 4px 16px rgba(21,128,61,0.3)",
            }}
          >
            Plan My Next Season →
          </button>
        </div>

        {/* ACTIONS */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          <button onClick={() => { setPhase("form"); setResult(null); setAgentMessages([]); }} style={{ padding: "16px", borderRadius: "12px", border: "2px solid #15803d", background: "white", color: "#15803d", fontSize: "16px", fontWeight: 700, cursor: "pointer" }}>
            ← Check Another Claim
          </button>
          <button onClick={() => window.print()} style={{ padding: "16px", borderRadius: "12px", border: "none", background: "#15803d", color: "white", fontSize: "16px", fontWeight: 700, cursor: "pointer" }}>
            🖨️ Print / Save Report
          </button>
        </div>
      </div>
    </main>
  );
}