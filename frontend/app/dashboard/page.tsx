"use client";

import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import styles from "./dashboard.module.css";

interface ScanEvent {
  type: string;
  data: Record<string, any>;
}

interface Bug {
  bug_id: string;
  severity: string;
  category: string;
  title: string;
  description: string;
  persona_name: string;
  persona_icon: string;
  element_name: string;
  chaos_input: string;
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const scanId = searchParams.get("scan_id") || "";
  const targetUrl = searchParams.get("url") || "";

  const [events, setEvents] = useState<ScanEvent[]>([]);
  const [bugs, setBugs] = useState<Bug[]>([]);
  const [status, setStatus] = useState<string>("connecting");
  const [chaosScore, setChaosScore] = useState<any>(null);
  const [progress, setProgress] = useState({ current: 0, total: 1, message: "" });
  const [stats, setStats] = useState({ actions: 0, bugsFound: 0, elapsed: 0 });
  const feedRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<any>(null);

  const addEvent = useCallback((event: ScanEvent) => {
    setEvents(prev => [...prev.slice(-200), event]);

    if (event.type === "bug") {
      const bug = event.data.bug;
      if (bug) setBugs(prev => [...prev, bug]);
      setStats(prev => ({ ...prev, bugsFound: prev.bugsFound + 1 }));
    }

    if (event.type === "action") {
      if (event.data.action === "filling" || event.data.action === "clicking") {
        setStats(prev => ({ ...prev, actions: prev.actions + 1 }));
      }
    }

    if (event.type === "progress") {
      setProgress({
        current: event.data.current_page || 0,
        total: event.data.total_pages || 1,
        message: event.data.message || "",
      });
    }

    if (event.type === "score") {
      setChaosScore(event.data.score);
      setStatus("completed");
    }

    if (event.type === "info" && event.data.message?.includes("Scan complete")) {
      setStatus("completed");
    }

    if (event.type === "error") {
      setStatus("error");
    }
  }, []);

  // WebSocket connection
  useEffect(() => {
    if (!scanId) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/${scanId}`);
    setStatus("connecting");

    ws.onopen = () => setStatus("running");

    ws.onmessage = (msg) => {
      try {
        const event: ScanEvent = JSON.parse(msg.data);
        if (event.type === "history") {
          const pastEvents = event.data.events || [];
          pastEvents.forEach((e: ScanEvent) => addEvent(e));
        } else if (event.type !== "connected") {
          addEvent(event);
        }
      } catch (e) { /* ignore parse errors */ }
    };

    ws.onerror = () => setStatus("error");
    ws.onclose = () => {
      if (status !== "completed") setStatus("disconnected");
    };

    // Timer
    const start = Date.now();
    timerRef.current = setInterval(() => {
      setStats(prev => ({ ...prev, elapsed: Math.floor((Date.now() - start) / 1000) }));
    }, 1000);

    return () => {
      ws.close();
      clearInterval(timerRef.current);
    };
  }, [scanId, addEvent]);

  // Auto-scroll feed
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [events]);

  const getStatusColor = () => {
    switch (status) {
      case "running": return "var(--neon-green)";
      case "completed": return "var(--neon-cyan)";
      case "error": return "var(--neon-red)";
      default: return "var(--neon-yellow)";
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "var(--neon-green)";
    if (score >= 60) return "var(--neon-cyan)";
    if (score >= 40) return "var(--neon-yellow)";
    if (score >= 20) return "var(--neon-orange)";
    return "var(--neon-red)";
  };

  const getSeverityClass = (sev: string) => `badge badge-${sev}`;

  return (
    <main className={styles.dashboard}>
      {/* ─── Top Bar ─── */}
      <header className={styles.topBar}>
        <div className={styles.topLeft}>
          <a href="/" className={styles.logo}>
            <span className="font-display">GREMLIN</span>
            <span className="text-red font-display">—AI</span>
          </a>
          <div className={styles.statusPill} style={{ borderColor: getStatusColor() }}>
            <span className="pulse-dot" style={{ background: getStatusColor(), boxShadow: `0 0 10px ${getStatusColor()}` }} />
            <span className="font-mono" style={{ color: getStatusColor() }}>
              {status.toUpperCase()}
            </span>
          </div>
        </div>
        <div className={styles.topRight}>
          <span className="font-mono text-muted" style={{ fontSize: 12 }}>
            TARGET: {targetUrl ? decodeURIComponent(targetUrl).substring(0, 40) : "N/A"}
          </span>
          <span className="font-mono text-cyan" style={{ fontSize: 12 }}>
            SCAN: {scanId}
          </span>
        </div>
      </header>

      {/* ─── Stats Bar ─── */}
      <div className={styles.statsBar}>
        <div className={styles.miniStat}>
          <span className={styles.miniStatValue}>{stats.actions}</span>
          <span className={styles.miniStatLabel}>Actions</span>
        </div>
        <div className={styles.miniStat}>
          <span className={`${styles.miniStatValue} ${bugs.length > 0 ? 'text-red' : 'text-green'}`}>
            {bugs.length}
          </span>
          <span className={styles.miniStatLabel}>Bugs Found</span>
        </div>
        <div className={styles.miniStat}>
          <span className={styles.miniStatValue}>
            {bugs.filter(b => b.severity === "critical").length}
          </span>
          <span className={styles.miniStatLabel}>Critical</span>
        </div>
        <div className={styles.miniStat}>
          <span className={styles.miniStatValue}>{stats.elapsed}s</span>
          <span className={styles.miniStatLabel}>Elapsed</span>
        </div>
        <div className={styles.miniStat}>
          <span className={styles.miniStatValue}>qwen-0.5b</span>
          <span className={styles.miniStatLabel}>Model</span>
        </div>
      </div>

      {status === "running" && (
        <div className={styles.progressWrap}>
          <div className="scan-line" />
        </div>
      )}

      {/* ─── Main Grid ─── */}
      <div className={styles.grid}>
        {/* Left: Live Feed */}
        <div className={`${styles.feedPanel} glass-card`}>
          <div className={styles.panelHeader}>
            <h3 className="font-mono text-cyan">LIVE GREMLIN FEED</h3>
            <span className="font-mono text-muted" style={{ fontSize: 11 }}>
              {events.length} events
            </span>
          </div>
          <div className={styles.feedScroll} ref={feedRef}>
            {events.map((event, i) => (
              <FeedItem key={i} event={event} />
            ))}
            {status === "running" && (
              <div className={styles.feedLine}>
                <span className="cursor-blink font-mono text-cyan" style={{ fontSize: 13 }}>
                  Scanning
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Bugs + Score */}
        <div className={styles.rightCol}>
          {/* Chaos Score */}
          {chaosScore && (
            <div className={`${styles.scorePanel} glass-card fade-in`}>
              <div className={styles.panelHeader}>
                <h3 className="font-mono text-cyan">GREMLIN SCORE</h3>
              </div>
              <div className={styles.scoreDisplay}>
                <div
                  className={styles.scoreCircle}
                  style={{
                    "--score-color": getScoreColor(chaosScore.score),
                    "--score-pct": `${chaosScore.score}%`,
                  } as React.CSSProperties}
                >
                  <svg viewBox="0 0 120 120" className={styles.scoreSvg}>
                    <circle cx="60" cy="60" r="52" className={styles.scoreTrack} />
                    <circle
                      cx="60" cy="60" r="52"
                      className={styles.scoreFill}
                      style={{
                        stroke: getScoreColor(chaosScore.score),
                        strokeDasharray: `${chaosScore.score * 3.27} 327`,
                      }}
                    />
                  </svg>
                  <div className={styles.scoreValue}>
                    <span style={{ color: getScoreColor(chaosScore.score) }}>
                      {Math.round(chaosScore.score)}
                    </span>
                    <small>/100</small>
                  </div>
                </div>
                <div className={styles.scoreGrade} style={{ color: getScoreColor(chaosScore.score) }}>
                  {chaosScore.grade}
                </div>
                <p className={styles.scoreVerdict}>{chaosScore.verdict}</p>
              </div>
            </div>
          )}

          {/* Bug List */}
          <div className={`${styles.bugPanel} glass-card`}>
            <div className={styles.panelHeader}>
              <h3 className="font-mono text-red">
                BUG REPORTS {bugs.length > 0 ? `(${bugs.length})` : ""}
              </h3>
            </div>
            <div className={styles.bugList}>
              {bugs.length === 0 ? (
                <p className="text-muted font-mono" style={{ padding: 20, textAlign: "center", fontSize: 13 }}>
                  {status === "running" ? "Hunting for bugs..." : "No bugs found yet"}
                </p>
              ) : (
                bugs.map((bug, i) => (
                  <div key={bug.bug_id || i} className={`${styles.bugCard} fade-in`}>
                    <div className={styles.bugHeader}>
                      <span className={getSeverityClass(bug.severity)}>
                        {bug.severity}
                      </span>
                      <span className="font-mono text-muted" style={{ fontSize: 10 }}>
                        {bug.bug_id}
                      </span>
                    </div>
                    <h4 className={styles.bugTitle}>{bug.title}</h4>
                    <p className={styles.bugDesc}>{bug.description?.substring(0, 120)}...</p>
                    <div className={styles.bugMeta}>
                      <span>{bug.persona_icon} {bug.persona_name}</span>
                      <span className="text-muted">|</span>
                      <span className="text-muted">{bug.element_name}</span>
                    </div>
                    {bug.chaos_input && (
                      <div className={styles.bugInput}>
                        <code>{bug.chaos_input.substring(0, 80)}</code>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

/* ─── Feed Item Component ─── */
function FeedItem({ event }: { event: ScanEvent }) {
  const { type, data } = event;

  if (type === "info") {
    return (
      <div className={styles.feedLine}>
        <span className="text-cyan font-mono" style={{ fontSize: 12 }}>
          {data.message}
        </span>
      </div>
    );
  }

  if (type === "action") {
    const icon = data.persona_icon || "🤖";
    const action = data.action || "?";
    const element = data.element || "";
    const input = data.input || "";

    let actionColor = "var(--text-secondary)";
    if (action === "filling") actionColor = "var(--neon-yellow)";
    if (action === "clicking") actionColor = "var(--neon-magenta)";
    if (action === "survived") actionColor = "var(--neon-green)";
    if (action === "generating_input") actionColor = "var(--text-muted)";

    return (
      <div className={styles.feedLine}>
        <span style={{ marginRight: 6 }}>{icon}</span>
        <span className="font-mono" style={{ color: actionColor, fontSize: 12 }}>
          {action}
        </span>
        <span className="font-mono text-muted" style={{ fontSize: 12 }}>
          {" "}&#39;{element}&#39;{" "}
        </span>
        {input && (
          <span className="font-mono" style={{ color: "var(--neon-yellow)", fontSize: 11, opacity: 0.7 }}>
            {input.substring(0, 45)}
          </span>
        )}
      </div>
    );
  }

  if (type === "bug") {
    return (
      <div className={`${styles.feedLine} ${styles.feedBug}`}>
        <span style={{ marginRight: 4 }}>🐛</span>
        <span className="font-mono text-red" style={{ fontSize: 12 }}>
          {data.message || "Bug found!"}
        </span>
      </div>
    );
  }

  if (type === "score") {
    const s = data.score || {};
    return (
      <div className={`${styles.feedLine} ${styles.feedScore}`}>
        <span className="font-mono text-cyan" style={{ fontSize: 13 }}>
          📊 GREMLIN SCORE: {s.score}/100 ({s.grade}) — {s.verdict}
        </span>
      </div>
    );
  }

  if (type === "progress") {
    return (
      <div className={styles.feedLine}>
        <span className="font-mono text-cyan" style={{ fontSize: 12 }}>
          {data.message}
        </span>
      </div>
    );
  }

  return null;
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh" }}>
        <span className="font-mono text-cyan cursor-blink">Summoning Gremlins</span>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
