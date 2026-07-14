"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, CheckCircle } from "lucide-react";

interface KrishiShiftResult {
  groundwater_status: string;
  groundwater_depth_mbgl: number;
  crop_risk_score: number;
  income_comparison: Record<string, number>;
  subsidies: any[];
  transition_plan: string;
}

type Phase = "form" | "streaming" | "results";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
const STATES = ["Maharashtra","Punjab","Madhya Pradesh","Rajasthan","Haryana","Andhra Pradesh","Telangana","Gujarat","Karnataka","Tamil Nadu","West Bengal","Uttar Pradesh","Bihar","Odisha","Chhattisgarh","Assam","Kerala","Jharkhand"];
const CROPS = ["Rice","Wheat","Cotton","Soybean","Maize","Tur","Groundnut","Bajra","Mustard","Gram","Sugarcane","Onion","Tomato","Banana"];

const friendlyMsg = (msg: string) => {
  if (/groundwater/i.test(msg)) return "Checking groundwater levels in your district...";
  if (/price|income|market/i.test(msg)) return "Comparing crop prices at your local mandi...";
  if (/subsidy|scheme/i.test(msg)) return "Finding government schemes you qualify for...";
  if (/plan|roadmap|transition/i.test(msg)) return "Building your 3-season farming roadmap...";
  return msg.replace(/[✅📝🌧️⚠️🔍📊🌱💰🗺️⏳]/g, "").trim();
};

export default function KrishiShiftPage() {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("form");
  const [agentMessages, setAgentMessages] = useState<string[]>([]);
  const [result, setResult] = useState<KrishiShiftResult | null>(null);
  const [error, setError] = useState("");
  const [showRoadmap, setShowRoadmap] = useState(true);
  const [form, setForm] = useState({
    farmer_name: "", district: "", state: "", crop: "", land_size_acres: 2,
  });

  const inputStyle: React.CSSProperties = {
    width: "100%", padding: "12px 16px", borderRadius: "8px",
    border: "1.5px solid #e5e7eb", fontSize: "15px", outline: "none",
    background: "white", color: "#1a1a1a", boxSizing: "border-box",
    fontFamily: "-apple-system, system-ui, sans-serif",
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPhase("streaming");
    setAgentMessages([]);
    setError("");
    try {
      const resp = await fetch(`${BACKEND_URL}/krishishift`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
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
      setError(err.message || "Connection failed.");
      setPhase("form");
    }
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
        <span style={{ fontSize: "20px", fontWeight: 900, color: "#15803d" }}>Krishi</span>
        <span style={{ fontSize: "20px", fontWeight: 900, color: "#d97706" }}>Shift</span>
      </div>
    </nav>
  );

  /* ── FORM ─────────────────────────── */
  if (phase === "form") return (
    <main style={{ background: "#fafaf5", minHeight: "100vh", paddingTop: "80px", fontFamily: "-apple-system, system-ui, sans-serif" }}>
      {nav}
      <div style={{ padding: "60px" }}>
        <p style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "3px", textTransform: "uppercase", color: "#d97706", marginBottom: "12px" }}>
          Free · No documents needed
        </p>
        <h1 style={{ fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 900, color: "#1a1a1a", marginBottom: "8px" }}>
          What should you grow next season?
        </h1>
        <p style={{ fontSize: "17px", color: "#6b7280", marginBottom: "40px" }}>
          Tell us where you are and what you grow. We'll check your groundwater, compare crop prices, and build your personal 3-season plan.
        </p>
        {error && (
          <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "12px", padding: "16px 20px", marginBottom: "24px", color: "#dc2626" }}>
            ⚠️ {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div style={{ background: "white", borderRadius: "16px", padding: "32px", marginBottom: "20px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
            <p style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "2px", textTransform: "uppercase", color: "#d97706", marginBottom: "24px" }}>Your Farm Details</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
              <div>
                <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>Your Name</label>
                <input style={inputStyle} placeholder="e.g. Suresh Patil" value={form.farmer_name} onChange={e => setForm(p => ({ ...p, farmer_name: e.target.value }))} required />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>Your District</label>
                <input style={inputStyle} placeholder="e.g. Wardha" value={form.district} onChange={e => setForm(p => ({ ...p, district: e.target.value }))} required />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>Your State</label>
                <select style={inputStyle} value={form.state} onChange={e => setForm(p => ({ ...p, state: e.target.value }))} required>
                  <option value="">Select your state...</option>
                  {STATES.map(s => <option key={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>What do you currently grow?</label>
                <select style={inputStyle} value={form.crop} onChange={e => setForm(p => ({ ...p, crop: e.target.value }))} required>
                  <option value="">Select crop...</option>
                  {CROPS.map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>How much land? (acres)</label>
                <input type="number" min="0.1" step="0.1" style={inputStyle} value={form.land_size_acres} onChange={e => setForm(p => ({ ...p, land_size_acres: parseFloat(e.target.value) }))} required />
              </div>
            </div>
          </div>
          <button type="submit" style={{
            width: "100%", padding: "18px", borderRadius: "12px", border: "none",
            background: "#d97706", color: "white", fontSize: "18px", fontWeight: 800,
            cursor: "pointer", boxShadow: "0 4px 20px rgba(217,119,6,0.3)",
          }}>
            Build My Farming Plan →
          </button>
        </form>
      </div>
    </main>
  );

  /* ── STREAMING ────────────────────── */
  if (phase === "streaming") return (
    <main style={{ background: "#fafaf5", minHeight: "100vh", paddingTop: "80px", fontFamily: "-apple-system, system-ui, sans-serif", display: "flex", alignItems: "center" }}>
      {nav}
      <div style={{ padding: "60px", maxWidth: "600px", margin: "0 auto", width: "100%", textAlign: "center" }}>
        <div style={{ width: "72px", height: "72px", borderRadius: "50%", background: "#fef3c7", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 24px", fontSize: "32px" }}>
          🌾
        </div>
        <h2 style={{ fontSize: "28px", fontWeight: 900, color: "#1a1a1a", marginBottom: "8px" }}>Building your farming plan...</h2>
        <p style={{ color: "#6b7280", marginBottom: "36px" }}>Checking your district's groundwater, mandi prices, and government schemes.</p>
        <div style={{ background: "white", borderRadius: "16px", padding: "24px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)", textAlign: "left" }}>
          {agentMessages.length === 0
            ? <p style={{ color: "#9ca3af" }}>Starting up...</p>
            : agentMessages.map((msg, i) => (
              <div key={i} style={{ display: "flex", gap: "12px", alignItems: "flex-start", padding: "10px 0", borderBottom: i < agentMessages.length - 1 ? "1px solid #f3f4f6" : "none" }}>
                <span>{i === agentMessages.length - 1 ? "⏳" : "✅"}</span>
                <span style={{ fontSize: "15px", color: i === agentMessages.length - 1 ? "#1a1a1a" : "#9ca3af", fontWeight: i === agentMessages.length - 1 ? 600 : 400 }}>
                  {friendlyMsg(msg)}
                </span>
              </div>
            ))}
        </div>
        <div style={{ marginTop: "20px", background: "#e5e7eb", borderRadius: "100px", height: "6px" }}>
          <div style={{ height: "6px", borderRadius: "100px", background: "#d97706", width: `${Math.min((agentMessages.length / 4) * 100, 95)}%`, transition: "width 0.5s ease" }} />
        </div>
        <p style={{ fontSize: "13px", color: "#9ca3af", marginTop: "8px" }}>Step {Math.min(agentMessages.length, 4)} of 4</p>
      </div>
    </main>
  );

  /* ── RESULTS ──────────────────────── */
  if (!result) return null;
  const incomeEntries = Object.entries(result.income_comparison || {});
  const maxIncome = Math.max(...incomeEntries.map(([, v]) => Number(v)));

  return (
    <main style={{ background: "#fafaf5", minHeight: "100vh", paddingTop: "80px", fontFamily: "-apple-system, system-ui, sans-serif" }}>
      {nav}
      <div style={{ padding: "60px" }}>

        {/* HERO */}
        <div style={{ background: "#fef9f0", border: "2px solid #fde68a", borderRadius: "20px", padding: "40px", marginBottom: "28px" }}>
          <p style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "3px", textTransform: "uppercase", color: "#d97706", marginBottom: "12px" }}>Your KrishiShift Plan</p>
          <h1 style={{ fontSize: "clamp(24px, 3vw, 36px)", fontWeight: 900, color: "#1a1a1a", marginBottom: "8px" }}>
            Here's how {form.farmer_name} can earn more next season
          </h1>
          <p style={{ fontSize: "16px", color: "#4b5563" }}>
            Based on groundwater, mandi prices, and government schemes for {form.district}, {form.state}.
          </p>
        </div>

        {/* GROUNDWATER + SUBSIDIES */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>
          <div style={{ background: "white", borderRadius: "16px", padding: "28px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
            <p style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "2px", textTransform: "uppercase", color: "#0369a1", marginBottom: "8px" }}>Groundwater in Your District</p>
            <p style={{ fontSize: "28px", fontWeight: 900, color: "#1a1a1a", textTransform: "capitalize", marginBottom: "4px" }}>{result.groundwater_status}</p>
            <p style={{ fontSize: "14px", color: "#4b5563" }}>Water table: {result.groundwater_depth_mbgl}m below ground</p>
            <div style={{ marginTop: "12px", padding: "10px 14px", background: result.groundwater_depth_mbgl > 10 ? "#fef2f2" : "#f0f9ff", borderRadius: "8px" }}>
              <span style={{ fontSize: "13px", color: result.groundwater_depth_mbgl > 10 ? "#dc2626" : "#0369a1", fontWeight: 600 }}>
                {result.groundwater_depth_mbgl > 10 ? "⚠️ Switch to low-water crops soon" : "✅ Water availability is manageable"}
              </span>
            </div>
          </div>
          <div style={{ background: "white", borderRadius: "16px", padding: "28px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
            <p style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "2px", textTransform: "uppercase", color: "#d97706", marginBottom: "12px" }}>Schemes You Qualify For</p>
            {(result.subsidies || []).slice(0, 4).map((s: any, i: number) => (
              <div key={i} style={{ display: "flex", gap: "8px", marginBottom: "8px", alignItems: "flex-start" }}>
                <CheckCircle size={14} style={{ color: "#15803d", marginTop: "2px", flexShrink: 0 }} />
                <span style={{ fontSize: "13px", color: "#374151" }}>{typeof s === "string" ? s : `${s.name} — ${s.amount}`}</span>
              </div>
            ))}
          </div>
        </div>

        {/* INCOME COMPARISON */}
        {incomeEntries.length > 0 && (
          <div style={{ background: "white", borderRadius: "16px", padding: "28px", marginBottom: "24px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
            <p style={{ fontSize: "14px", fontWeight: 700, color: "#374151", marginBottom: "16px" }}>
              Crop income comparison in your area (₹ per acre)
            </p>
            {incomeEntries.map(([crop, val], i) => {
              const isCurrent = crop.toLowerCase() === form.crop.toLowerCase();
              return (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" }}>
                  <span style={{ fontSize: "14px", color: "#374151", minWidth: "100px", textTransform: "capitalize" }}>
                    {crop} {isCurrent ? <span style={{ fontSize: "11px", color: "#d97706" }}>(current)</span> : ""}
                  </span>
                  <div style={{ flex: 1, background: "#f3f4f6", borderRadius: "100px", height: "14px" }}>
                    <div style={{ height: "14px", borderRadius: "100px", background: isCurrent ? "#d97706" : "#15803d", width: `${(Number(val) / maxIncome) * 100}%`, transition: "width 1s ease" }} />
                  </div>
                  <span style={{ fontSize: "14px", fontWeight: 700, color: isCurrent ? "#d97706" : "#15803d", minWidth: "70px", textAlign: "right" }}>
                    ₹{Number(val).toLocaleString()}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {/* 3-SEASON ROADMAP */}
        {result.transition_plan && (
          <div style={{ background: "white", borderRadius: "16px", padding: "32px", marginBottom: "24px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
            <h3 style={{ fontSize: "20px", fontWeight: 900, color: "#1a1a1a", marginBottom: "20px" }}>🗺️ Your 3-Season Plan</h3>
            {(() => {
              const clean = result.transition_plan.replace(/\*\*/g, "");
              const seasons = [
                { label: "Season 1 — Right Now", emoji: "🌱", color: "#15803d", bg: "#f0fdf4", border: "#bbf7d0" },
                { label: "Season 2 — Next Season", emoji: "🌿", color: "#0369a1", bg: "#f0f9ff", border: "#bae6fd" },
                { label: "Season 3 — Target", emoji: "🎯", color: "#d97706", bg: "#fef9f0", border: "#fde68a" },
              ];
              return seasons.map((s, i) => {
                const start = clean.search(new RegExp(`Season ${i + 1}`, "i"));
                if (start === -1) return null;
                const end = i < 2 ? clean.search(new RegExp(`Season ${i + 2}`, "i")) : clean.length;
                let content = clean.slice(start, end > -1 ? end : clean.length);
                content = content.replace(/^Season \d+[^:]*:\s*/i, "").trim();
                const bullets = content.split(/\.\s+/).filter(p => p.trim().length > 10);
                return (
                  <div key={i} style={{ background: s.bg, border: `1px solid ${s.border}`, borderRadius: "12px", padding: "20px 24px", marginBottom: "12px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                      <span style={{ fontSize: "18px" }}>{s.emoji}</span>
                      <h4 style={{ fontSize: "15px", fontWeight: 800, color: s.color }}>{s.label}</h4>
                    </div>
                    {bullets.map((point, j) => (
                      <div key={j} style={{ display: "flex", gap: "10px", marginBottom: "8px", alignItems: "flex-start" }}>
                        <span style={{ color: s.color, fontWeight: 900, flexShrink: 0 }}>→</span>
                        <span style={{ fontSize: "14px", color: "#374151", lineHeight: 1.7 }}>
                          {point.trim().endsWith(".") ? point.trim() : point.trim() + "."}
                        </span>
                      </div>
                    ))}
                  </div>
                );
              });
            })()}
          </div>
        )}

        {/* ACTIONS */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          <button onClick={() => { setPhase("form"); setResult(null); setAgentMessages([]); }} style={{ padding: "16px", borderRadius: "12px", border: "2px solid #d97706", background: "white", color: "#d97706", fontSize: "16px", fontWeight: 700, cursor: "pointer" }}>
            ← Plan for Another Farm
          </button>
          <button onClick={() => router.push("/analyze")} style={{ padding: "16px", borderRadius: "12px", border: "none", background: "#15803d", color: "white", fontSize: "16px", fontWeight: 700, cursor: "pointer" }}>
            Also Check My Insurance Claim →
          </button>
        </div>
      </div>
    </main>
  );
}