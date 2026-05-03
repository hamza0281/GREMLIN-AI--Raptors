"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import styles from "./page.module.css";

const PERSONAS = [
  { id: "confused_grandma", icon: "👵", name: "Confused Grandma", desc: "Wrong inputs everywhere", color: "#ff9fcc" },
  { id: "accidental_hacker", icon: "🏴‍☠️", name: "Accidental Hacker", desc: "XSS, SQLi, injections", color: "#ff0040" },
  { id: "speed_demon", icon: "⚡", name: "Speed Demon", desc: "Race conditions & spam", color: "#ffd000" },
  { id: "toddler", icon: "🧒", name: "Toddler", desc: "Pure keyboard chaos", color: "#00ff88" },
  { id: "overthinking_dev", icon: "🤓", name: "Overthinking Dev", desc: "JSON, code, long strings", color: "#a855f7" },
  { id: "international_traveler", icon: "🌍", name: "Intl. Traveler", desc: "Unicode & i18n chaos", color: "#00f0ff" },
];

// Live attack ticker — simulated telemetry feed
const TICKER_ITEMS = [
  { persona: "🏴‍☠️", action: "filling", field: "email", payload: "<script>alert(document.cookie)</script>", result: "XSS_DETECTED", sev: "MEDIUM" },
  { persona: "👵", action: "filling", field: "phone", payload: "My grandson showed me how to use the internets", result: "INVALID_FORMAT", sev: "LOW" },
  { persona: "🧒", action: "filling", field: "password", payload: "asdfjkl;qweruiop1234💀💀💀", result: "VALIDATION_BYPASS", sev: "LOW" },
  { persona: "🏴‍☠️", action: "filling", field: "search", payload: "' OR 1=1; DROP TABLE users; --", result: "SQLI_DETECTED", sev: "CRITICAL" },
  { persona: "⚡", action: "clicking", field: "Submit", payload: "×47 rapid clicks", result: "RACE_CONDITION", sev: "HIGH" },
  { persona: "🤓", action: "filling", field: "username", payload: '{"$gt":"","$where":"this.password.length>0"}', result: "NOSQLI_DETECTED", sev: "HIGH" },
  { persona: "🌍", action: "filling", field: "name", payload: "الاسم؟ 你好 مرحبا 🎭🔥", result: "UNICODE_OVERFLOW", sev: "LOW" },
  { persona: "🏴‍☠️", action: "filling", field: "url", payload: "javascript:alert(1)//https://legit.com", result: "PROTO_INJECTION", sev: "HIGH" },
  { persona: "🤓", action: "filling", field: "age", payload: "9".repeat(500), result: "BUFFER_OVERFLOW", sev: "MEDIUM" },
  { persona: "👵", action: "filling", field: "date", payload: "Tuesday the 47th of Octember", result: "PARSE_ERROR", sev: "LOW" },
];

const SEV_COLORS: Record<string, string> = {
  CRITICAL: "#ff0040",
  HIGH: "#ff6600",
  MEDIUM: "#ffd000",
  LOW: "#00ff88",
};

// Counter animation hook — starts on mount
function useCountUp(target: number, duration = 1800) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const start = performance.now();
    const step = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(ease * target));
      if (progress < 1) requestAnimationFrame(step);
      else setCount(target);
    };
    // Slight delay to let page render first
    const t = setTimeout(() => requestAnimationFrame(step), 1200);
    return () => clearTimeout(t);
  }, [target, duration]);

  return { count, ref };
}

// Glitch text component — direct span, gradient via CSS
function GlitchText({ text, className }: { text: string; className?: string }) {
  return (
    <span className={`${styles.glitchWrap} ${className || ""}`} data-text={text}>
      {text}
    </span>
  );
}

// Live ticker row
function TickerRow({ item, index }: { item: typeof TICKER_ITEMS[0]; index: number }) {
  return (
    <div className={styles.tickerRow} style={{ animationDelay: `${index * 0.08}s` }}>
      <span className={styles.tickerPersona}>{item.persona}</span>
      <span className={styles.tickerAction}>{item.action}</span>
      <span className={styles.tickerField}>'{item.field}'</span>
      <span className={styles.tickerPayload}>{item.payload.substring(0, 35)}</span>
      <span
        className={styles.tickerResult}
        style={{ color: SEV_COLORS[item.sev] }}
      >
        [{item.sev}] {item.result}
      </span>
    </div>
  );
}

export default function Home() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [selectedPersonas, setSelectedPersonas] = useState<string[]>(PERSONAS.map(p => p.id));
  const [isLaunching, setIsLaunching] = useState(false);
  const [tickerIndex, setTickerIndex] = useState(0);
  const [mounted, setMounted] = useState(false);

  const bugsCount = useCountUp(12847);
  const scansCount = useCountUp(934);
  const xssCount = useCountUp(3291);
  const critCount = useCountUp(489);

  useEffect(() => {
    setMounted(true);
    const interval = setInterval(() => {
      setTickerIndex(prev => (prev + 1) % TICKER_ITEMS.length);
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  const togglePersona = (id: string) => {
    setSelectedPersonas(prev =>
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    );
  };

  const launchScan = async () => {
    if (!url.trim()) return;
    let targetUrl = url.trim();
    if (!targetUrl.startsWith("http")) targetUrl = "https://" + targetUrl;
    setIsLaunching(true);
    try {
      const resp = await fetch("http://localhost:8000/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: targetUrl,
          personas: selectedPersonas,
          max_actions_per_element: 2,
          max_pages: 1,
        }),
      });
      const data = await resp.json();
      if (data.scan_id) {
        router.push(`/dashboard?scan_id=${data.scan_id}&url=${encodeURIComponent(targetUrl)}`);
      }
    } catch (err) {
      console.error("Failed to start scan:", err);
      setIsLaunching(false);
    }
  };

  return (
    <main className={styles.main}>

      {/* ══════════════════════════════════════════════
          HERO SECTION
      ══════════════════════════════════════════════ */}
      <section className={styles.hero}>
        {/* Radial hero glow */}
        <div className={styles.heroGlow} />
        <div className={styles.heroGlowRed} />

        <div className={`${styles.heroContent} ${mounted ? styles.heroVisible : ""}`}>

          {/* ── Live Status Badge ── */}
          <div className={styles.liveBadge}>
            <span className={styles.liveDot} />
            <span>LIVE · 934 scans running · 12,847 bugs found today</span>
          </div>

          {/* ── Main Title ── */}
          <h1 className={styles.heroTitle}>
            <span className={styles.heroTitleTop}>GREMLIN</span>
            <span className={styles.heroTitleBottom}>
              <span className={styles.heroDash}>—</span>
              <span className={styles.heroAI}>AI</span>
            </span>
          </h1>

          {/* ── Hero Tagline ── */}
          <p className={styles.heroTagline}>
            The AI that{" "}
            <span className={styles.taglineBreak}>breaks your app</span>
            {" "}before your users do
          </p>

          {/* ── Sub description ── */}
          <p className={styles.heroDesc}>
            A <strong className="text-cyan">0.5B model's hallucinations</strong> are its superpower —
            not a flaw. Feed it your app. Watch it find bugs{" "}
            <strong className="text-red">ChatGPT never would.</strong>
          </p>

          {/* ── Feature Pills ── */}
          <div className={styles.featurePills}>
            {[
              { icon: "🆓", label: "$0 cost · Local Ollama" },
              { icon: "⚡", label: "No API key needed" },
              { icon: "🎭", label: "6 AI attack personas" },
              { icon: "🔍", label: "XSS · SQLi · Race conditions" },
              { icon: "📋", label: "Auto bug reports" },
            ].map(p => (
              <span key={p.label} className={styles.featurePill}>
                {p.icon} {p.label}
              </span>
            ))}
          </div>

          {/* ── Hero CTA ── */}
          <div className={styles.heroCTA}>
            <div className={styles.heroInputWrap}>
              <div className={styles.heroInputPrefix}>TARGET://</div>
              <input
                type="text"
                className={`neon-input ${styles.heroInput}`}
                placeholder="https://your-webapp.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && launchScan()}
              />
            </div>
            <button
              id="hero-launch-btn"
              className={styles.heroLaunchBtn}
              onClick={launchScan}
              disabled={!url.trim() || isLaunching}
            >
              {isLaunching ? (
                <><span className={styles.btnSpinner} />SUMMONING...</>
              ) : (
                <>👾 SUMMON THE GREMLINS</>
              )}
              <span className={styles.btnGlow} />
            </button>
          </div>
          <p className={styles.heroNote}>
            No signup · Runs 100% locally · Open source
          </p>
        </div>

        {/* ── Live Attack Terminal Preview ── */}
        <div className={`${styles.heroTerminal} ${mounted ? styles.terminalVisible : ""}`}>
          <div className={styles.terminalBar}>
            <span className={styles.terminalDot} style={{ background: "#ff5f57" }} />
            <span className={styles.terminalDot} style={{ background: "#febc2e" }} />
            <span className={styles.terminalDot} style={{ background: "#28c840" }} />
            <span className={styles.terminalTitle}>gremlin-ai — live attack stream</span>
          </div>
          <div className={styles.terminalBody}>
            <div className={styles.terminalPrompt}>
              <span className="text-cyan font-mono">$</span>
              <span className="font-mono text-muted"> gremlin scan --target https://example.com --personas all</span>
            </div>
            <div className={styles.tickerFeed}>
              {TICKER_ITEMS.slice(tickerIndex, tickerIndex + 5).concat(
                TICKER_ITEMS.slice(0, Math.max(0, 5 - (TICKER_ITEMS.length - tickerIndex)))
              ).map((item, i) => (
                <TickerRow key={`${tickerIndex}-${i}`} item={item} index={i} />
              ))}
            </div>
            <div className={styles.terminalCursor}>
              <span className="text-green font-mono">→</span>
              <span className="font-mono text-cyan" style={{ fontSize: 11 }}> scan running</span>
              <span className={styles.cursorBlink}>_</span>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════
          SOCIAL PROOF STATS BAR
      ══════════════════════════════════════════════ */}
      <section className={styles.proofBar}>
        <div className={styles.proofDivider} />
        <div className={styles.proofGrid}>
          <div className={styles.proofStat} ref={bugsCount.ref}>
            <div className={styles.proofValue}>{bugsCount.count.toLocaleString()}+</div>
            <div className={styles.proofLabel}>Bugs Smashed</div>
          </div>
          <div className={styles.proofStat} ref={scansCount.ref}>
            <div className={styles.proofValue}>{scansCount.count}+</div>
            <div className={styles.proofLabel}>Apps Scanned</div>
          </div>
          <div className={styles.proofStat} ref={xssCount.ref}>
            <div className={`${styles.proofValue} ${styles.proofRed}`}>{xssCount.count.toLocaleString()}</div>
            <div className={styles.proofLabel}>XSS Vectors Found</div>
          </div>
          <div className={styles.proofStat} ref={critCount.ref}>
            <div className={`${styles.proofValue} ${styles.proofOrange}`}>{critCount.count}</div>
            <div className={styles.proofLabel}>Critical Bugs</div>
          </div>
          <div className={styles.proofStat}>
            <div className={styles.proofValue}>$0</div>
            <div className={styles.proofLabel}>Operational Cost</div>
          </div>
          <div className={styles.proofStat}>
            <div className={styles.proofValue}>0.5B</div>
            <div className={styles.proofLabel}>Model Parameters</div>
          </div>
        </div>
        <div className={styles.proofDivider} />
      </section>

      {/* ══════════════════════════════════════════════
          LAUNCH PANEL
      ══════════════════════════════════════════════ */}
      <section className={styles.launchSection}>
        <div className={`${styles.launchPanel} glass-card`}>
          <div className={styles.launchHeader}>
            <h2 className="font-display">INITIATE CHAOS</h2>
            <p className="text-muted">Enter target URL. Set your gremlins. Watch them wreak havoc.</p>
          </div>
          <div className={styles.inputGroup}>
            <div className={styles.inputPrefix}>TARGET://</div>
            <input
              type="text"
              className={`neon-input ${styles.urlInput}`}
              placeholder="https://your-webapp.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && launchScan()}
            />
          </div>
          <div className={styles.personaGrid}>
            {PERSONAS.map((persona) => (
              <button
                key={persona.id}
                className={`${styles.personaCard} ${selectedPersonas.includes(persona.id) ? styles.personaActive : ""}`}
                onClick={() => togglePersona(persona.id)}
                style={{ "--persona-color": persona.color } as React.CSSProperties}
              >
                <span className={styles.personaIcon}>{persona.icon}</span>
                <span className={styles.personaName}>{persona.name}</span>
                <span className={styles.personaDesc}>{persona.desc}</span>
                {selectedPersonas.includes(persona.id) && <span className={styles.personaCheck}>✓</span>}
              </button>
            ))}
          </div>
          <button
            className={`btn-neon btn-large btn-red ${styles.launchBtn}`}
            onClick={launchScan}
            disabled={!url.trim() || isLaunching}
          >
            {isLaunching ? (
              <><span className={styles.spinner} />SUMMONING GREMLINS...</>
            ) : (
              <>👾 SUMMON THE GREMLINS</>
            )}
          </button>
        </div>
      </section>

      {/* ══════════════════════════════════════════════
          HOW IT WORKS
      ══════════════════════════════════════════════ */}
      <section className={styles.howSection}>
        <div className={styles.howHeader}>
          <span className={styles.howPre}>THE PIPELINE</span>
          <h2 className={`${styles.sectionTitle} font-display`}>HOW IT WORKS</h2>
          <p className={styles.howSub}>6 steps from URL to professional bug report</p>
        </div>
        <div className={styles.howGrid}>
          {[
            { step: "01", icon: "🌐", title: "Crawl", desc: "Playwright discovers every form, button, and link on your target" },
            { step: "02", icon: "🎭", title: "Personas", desc: "6 AI personas attack with contextual chaos — not random noise" },
            { step: "03", icon: "🧠", title: "Generate", desc: "0.5B model hallucinates inputs — its confusion IS the test" },
            { step: "04", icon: "💥", title: "Execute", desc: "Fill forms, click buttons, submit — watch your app struggle" },
            { step: "05", icon: "🔍", title: "Detect", desc: "Console errors, XSS alerts, crashes, network failures captured" },
            { step: "06", icon: "📋", title: "Report", desc: "Professional bug reports with severity, screenshots, repro steps" },
          ].map((item, i) => (
            <div key={item.step} className={`${styles.howCard} glass-card fade-in stagger-${Math.min(i + 1, 5)}`}>
              <div className={styles.howStep}>{item.step}</div>
              <div className={styles.howIcon}>{item.icon}</div>
              <h3>{item.title}</h3>
              <p>{item.desc}</p>
              {i < 5 && <div className={styles.howConnector} />}
            </div>
          ))}
        </div>
      </section>

      {/* ══════════════════════════════════════════════
          FOOTER
      ══════════════════════════════════════════════ */}
      <footer className={styles.footer}>
        <div className={styles.footerGlow} />
        <p className="font-mono text-muted">
          GREMLIN-AI v1.0 · GARAGE_INFERENCE 2026 · Qwen 0.5B · Tier 1 Absolute Garage
        </p>
        <p className="text-muted" style={{ fontSize: 12, marginTop: 6 }}>
          &quot;Grmlins wreck machines. Our AI wrecks your bugs. Every time.&quot;
        </p>
      </footer>
    </main>
  );
}
