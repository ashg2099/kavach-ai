"use client";
import { useRouter } from "next/navigation";
import { ArrowRight, CheckCircle } from "lucide-react";

export default function Home() {
  const router = useRouter();

  return (
    <main style={{ background: "#ffffff", color: "#1a1a1a", fontFamily: "-apple-system, system-ui, sans-serif" }}>

      {/* NAV */}
      <nav style={{
        position: "fixed", top: 0, left: 0, right: 0, zIndex: 50,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "16px 60px", background: "rgba(255,255,255,0.95)",
        backdropFilter: "blur(10px)", borderBottom: "1px solid #e5e7eb",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "22px", fontWeight: 900, color: "#15803d" }}>Kavach</span>
          <span style={{ fontSize: "22px", fontWeight: 900, color: "#d97706" }}>AI</span>
        </div>
        <button onClick={() => router.push("/analyze")}
          style={{
            display: "flex", alignItems: "center", gap: "8px",
            padding: "10px 22px", borderRadius: "8px", border: "none",
            background: "#15803d", color: "white", fontWeight: 700,
            fontSize: "14px", cursor: "pointer",
          }}>
          Check My Claim <ArrowRight size={16} />
        </button>
      </nav>

      {/* HERO */}
      <section style={{ paddingTop: "80px", minHeight: "90vh", display: "flex", flexDirection: "column" }}>
        <div style={{ background: "#d97706", padding: "60px 60px 0" }}>
          <p style={{ color: "rgba(255,255,255,0.75)", fontSize: "13px", fontWeight: 600, letterSpacing: "2px", textTransform: "uppercase", marginBottom: "16px" }}>
            For farmers across India
          </p>
          <h1 style={{ fontSize: "clamp(28px, 3.5vw, 52px)", fontWeight: 900, color: "white", lineHeight: 2.00, maxWidth: "1300px" }}>
            Your crop failed. You deserve what's owed to you.
          </h1>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", flexGrow: 1 }}>
          <div style={{ background: "#fef9f0", padding: "52px 60px 64px", display: "flex", flexDirection: "column", justifyContent: "center" }}>
            <p style={{ fontSize: "18px", lineHeight: 1.8, color: "#4b5563", marginBottom: "20px" }}>
              Small and marginal farmers grow 85% of India's food. When a flood, drought,
              or unseasonal rain destroys the harvest, most farmers never receive the
              insurance money they legally paid for — not because they don't qualify,
              but because no one helped them navigate the process.
            </p>
            <p style={{ fontSize: "18px", lineHeight: 1.8, color: "#4b5563", marginBottom: "36px" }}>
              <strong style={{ color: "#15803d" }}>Kavach AI is that help.</strong> Tell us what happened.
              We verify the weather, check your coverage, calculate what you're owed,
              and write your claim letter — in under 2 minutes.
            </p>
            <button onClick={() => router.push("/analyze")}
              style={{
                display: "inline-flex", alignItems: "center", gap: "10px",
                padding: "16px 32px", borderRadius: "10px", border: "none",
                background: "#15803d", color: "white", fontWeight: 800,
                fontSize: "17px", cursor: "pointer", alignSelf: "flex-start",
                boxShadow: "0 4px 20px rgba(21,128,61,0.3)",
              }}>
              Check My Claim Now <ArrowRight size={20} />
            </button>
            <p style={{ marginTop: "12px", fontSize: "13px", color: "#9ca3af" }}>
              Free · 2 minutes · No documents needed to start
            </p>
          </div>
          <div style={{ overflow: "hidden" }}>
            <img
              src="https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=900&q=80"
              alt="Farmer in green fields"
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </div>
        </div>
      </section>

      {/* STORY SECTION */}
      <section style={{ padding: "80px 60px", background: "#ffffff" }}>
        <p style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "3px", textTransform: "uppercase", color: "#d97706", marginBottom: "20px" }}>
          A story you may recognise
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "64px", alignItems: "center" }}>
          <div>
            <h2 style={{ fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 900, color: "#1a1a1a", marginBottom: "28px", lineHeight: 1.2 }}>
              Ramesh grows soybean in Vidisha, Madhya Pradesh.
            </h2>
            <p style={{ fontSize: "17px", lineHeight: 1.9, color: "#4b5563", marginBottom: "18px" }}>
              This July, three weeks of continuous rain flooded his fields. He lost nearly 70% of his crop.
              His family had been counting on that harvest for the year.
            </p>
            <p style={{ fontSize: "17px", lineHeight: 1.9, color: "#4b5563", marginBottom: "18px" }}>
              Ramesh knew he had PMFBY insurance — his bank deducted the premium every season.
              But when he went to file a claim, he was handed forms he didn't understand,
              asked for documents he didn't have, and told to come back next week.
            </p>
            <p style={{ fontSize: "17px", lineHeight: 1.9, color: "#4b5563", marginBottom: "24px" }}>
              He came back three times. Each time, a different answer.
            </p>
            <div style={{
              background: "#f0fdf4", border: "1px solid #bbf7d0",
              borderRadius: "12px", padding: "20px 24px",
            }}>
              <p style={{ fontSize: "18px", fontWeight: 700, color: "#15803d", margin: 0 }}>
                Ramesh is entitled to ₹56,000.<br />
                <span style={{ fontWeight: 400, color: "#374151" }}>He just needed someone in his corner.</span>
              </p>
            </div>
          </div>
          <div style={{ borderRadius: "16px", overflow: "hidden", boxShadow: "0 20px 60px rgba(0,0,0,0.12)" }}>
            <img
              src="https://images.unsplash.com/photo-1625246333195-d7b7e3b5e9a6?w=700&q=80"
              alt="Indian farmer in field"
              onError={(e) => {
                (e.target as HTMLImageElement).src = "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=700&q=80";
              }}
              style={{ width: "100%", height: "420px", objectFit: "cover" }}
            />
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section style={{ padding: "80px 60px", background: "#f9fafb" }}>
        <p style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "3px", textTransform: "uppercase", color: "#d97706", marginBottom: "12px" }}>
          How it works
        </p>
        <h2 style={{ fontSize: "clamp(28px, 4vw, 42px)", fontWeight: 900, color: "#1a1a1a", marginBottom: "48px" }}>
          Three things. In plain language.
        </h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {[
            {
              num: "01",
              title: "We check if you are covered",
              body: "We look up whether your crop, in your state, is covered under PMFBY for this season. In seconds. No paperwork needed from you yet.",
            },
            {
              num: "02",
              title: "We verify the weather using official records",
              body: "We pull real rainfall and weather data for your district from government weather archives. This is the proof your insurance company needs to pay your claim.",
            },
            {
              num: "03",
              title: "We calculate what you're owed and write your claim letter",
              body: "Based on your land size and crop loss, we calculate your exact entitlement and generate a formal claim letter — ready to hand to your bank or insurance company.",
            },
          ].map(step => (
            <div key={step.num} style={{
              display: "flex", gap: "28px", alignItems: "flex-start",
              background: "white", borderRadius: "16px",
              padding: "28px 32px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
            }}>
              <div style={{
                fontSize: "36px", fontWeight: 900, color: "#d97706",
                fontFamily: "monospace", lineHeight: 1, minWidth: "52px",
              }}>
                {step.num}
              </div>
              <div>
                <h3 style={{ fontSize: "20px", fontWeight: 800, color: "#1a1a1a", marginBottom: "8px" }}>
                  {step.title}
                </h3>
                <p style={{ fontSize: "16px", lineHeight: 1.7, color: "#6b7280", margin: 0 }}>
                  {step.body}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* KRISHISHIFT SECTION */}
        <section style={{ padding: "80px 60px", background: "#ffffff" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "80px", alignItems: "center" }}>
            <div>
            <img
                src="https://images.pexels.com/photos/2933243/pexels-photo-2933243.jpeg"
                alt="Farmer planning next season"
                style={{ width: "100%", height: "420px", objectFit: "cover", borderRadius: "20px" }}
                onError={(e) => { (e.target as HTMLImageElement).src = "https://picsum.photos/seed/farmer2/600/420"; }}
            />
            </div>
            <div>
            <p style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "3px", textTransform: "uppercase", color: "#d97706", marginBottom: "16px" }}>
                Introducing KrishiShift
            </p>
            <h2 style={{ fontSize: "clamp(28px, 3vw, 42px)", fontWeight: 900, color: "#1a1a1a", lineHeight: 1.2, marginBottom: "24px" }}>
                Suresh claimed ₹45,000 last year.<br />
                <span style={{ color: "#dc2626" }}>Then planted cotton again.</span>
            </h2>
            <p style={{ fontSize: "17px", color: "#4b5563", lineHeight: 1.8, marginBottom: "16px" }}>
                Drought came again. Same loss, again. Nobody told Suresh that his district's groundwater had dropped 4 metres. Nobody showed him that Tur dal earns 40% more per acre in his mandi. Nobody told him the government had a 90% subsidy on drip irrigation waiting for him.
            </p>
            <p style={{ fontSize: "17px", color: "#4b5563", lineHeight: 1.8, marginBottom: "32px" }}>
                <strong style={{ color: "#1a1a1a" }}>KrishiShift does.</strong> It looks at your groundwater, your local crop prices, and the subsidies you already qualify for — then builds you a 3-season plan to earn more and risk less.
            </p>
            <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "20px" }}>
                {["Groundwater check", "Crop price comparison", "3-season roadmap"].map((item, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <span style={{ color: "#15803d", fontSize: "16px" }}>✓</span>
                    <span style={{ fontSize: "14px", color: "#4b5563", fontWeight: 500 }}>{item}</span>
                </div>
                ))}
            </div>
            <button
                onClick={() => router.push("/krishishift")}
                style={{
                padding: "16px 32px", borderRadius: "10px", border: "none",
                background: "#d97706", color: "white", fontSize: "17px",
                fontWeight: 800, cursor: "pointer", display: "inline-flex",
                alignItems: "center", gap: "8px",
                boxShadow: "0 4px 20px rgba(217,119,6,0.3)",
                }}
            >
                Plan My Next Season →
            </button>
            </div>
        </div>
        </section>

      {/* WHAT YOU GET */}
      <section style={{ padding: "80px 60px", background: "#fef9f0" }}>
        <p style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "3px", textTransform: "uppercase", color: "#d97706", marginBottom: "12px" }}>
          What you walk away with
        </p>
        <h2 style={{ fontSize: "clamp(28px, 4vw, 42px)", fontWeight: 900, color: "#1a1a1a", marginBottom: "40px" }}>
          At the end, you will have
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
          {[
            { emoji: "📄", title: "Your claim letter", body: "A formal, ready-to-submit insurance claim with all required details filled in. Just print and hand it over." },
            { emoji: "🌧️", title: "Official weather proof", body: "Real government weather records for your district confirming the event that damaged your crop." },
            { emoji: "⚖️", title: "Your legal rights", body: "A clear explanation of what the insurance company must do — and by when — under PMFBY rules." },
            { emoji: "🗺️", title: "A 3-season plan", body: "A practical roadmap for moving to a more stable and profitable crop, with the subsidies to fund it." },
          ].map(item => (
            <div key={item.title} style={{
              background: "white", borderRadius: "16px", padding: "28px",
              boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
            }}>
              <div style={{ fontSize: "32px", marginBottom: "14px" }}>{item.emoji}</div>
              <h3 style={{ fontSize: "18px", fontWeight: 800, color: "#1a1a1a", marginBottom: "10px" }}>{item.title}</h3>
              <p style={{ fontSize: "15px", lineHeight: 1.7, color: "#6b7280", margin: 0 }}>{item.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FINAL CTA */}
      <section style={{ padding: "80px 60px", background: "#15803d" }}>
        <h2 style={{ fontSize: "clamp(28px, 4vw, 52px)", fontWeight: 900, color: "white", lineHeight: 1.2, marginBottom: "16px" }}>
          You grew the crop.<br />
          You paid the premium.<br />
          You deserve the payout.
        </h2>
        <p style={{ fontSize: "18px", color: "rgba(255,255,255,0.75)", marginBottom: "36px" }}>
          It takes two minutes. No documents needed to start.
        </p>
        <button onClick={() => router.push("/analyze")}
          style={{
            display: "inline-flex", alignItems: "center", gap: "12px",
            padding: "18px 40px", borderRadius: "12px", border: "2px solid white",
            background: "white", color: "#15803d", fontWeight: 800,
            fontSize: "18px", cursor: "pointer",
            boxShadow: "0 8px 30px rgba(0,0,0,0.2)",
          }}>
          Start My Claim Check <ArrowRight size={22} />
        </button>
      </section>

      {/* FOOTER */}
      <footer style={{ padding: "40px 60px", background: "#1a1a1a" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "10px" }}>
          <span style={{ fontSize: "18px", fontWeight: 900, color: "#4ade80" }}>Kavach</span>
          <span style={{ fontSize: "18px", fontWeight: 900, color: "#fbbf24" }}>AI</span>
        </div>
        <p style={{ fontSize: "12px", color: "#6b7280", marginBottom: "6px" }}>
          Built for Deutsche Telekom Digital Labs — The Talent Hack 2026
        </p>
        <p style={{ fontSize: "11px", color: "#4b5563" }}>
          Powered by LangGraph · LangChain · RAG · Groq LLaMA 3.3 · FastAPI · Open-Meteo · Agmarknet
        </p>
      </footer>
    </main>
  );
}