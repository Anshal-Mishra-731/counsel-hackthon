import { Link } from "react-router-dom";
import { ChokepointMark } from "../components/Header";
import { sampleData } from "../lib/sampleData";
import { tierForSeverity, TIER_COLOR_VAR } from "../lib/format";

const AGENTS = [
  {
    title: "Geopolitical Risk Intelligence Agent",
    desc: "Turns news, shipping-traffic and sanctions signals into a live disruption-probability score for every corridor and supplier.",
    status: "live",
    icon: <IconRadar />,
  },
  {
    title: "Disruption Scenario Modeller",
    desc: "Simulates a Hormuz closure, a Red Sea suspension, or anything in between, and traces the cascade through refining, price and reserves.",
    status: "live",
    icon: <IconWave />,
  },
  {
    title: "Supply Chain Digital Twin",
    desc: "A geospatial model of the network — every route, chokepoint and supplier plotted, so a what-if stays visual, not just tabular.",
    status: "live",
    icon: <IconGlobe />,
  },
  {
    title: "Adaptive Procurement Orchestrator",
    desc: "Ranks alternative crude sources and logistics routes so procurement teams can act within hours, not weeks.",
    status: "roadmap",
    icon: <IconRoute />,
  },
  {
    title: "Strategic Reserve Optimisation Agent",
    desc: "Models optimal reserve-drawdown schedules against forecast supply gaps, so the 9.5-day cushion is spent on purpose.",
    status: "roadmap",
    icon: <IconGauge />,
  },
];

const PIPELINE = [
  {
    n: "01",
    title: "Score the risk",
    desc: "The risk intelligence agent reads live signals per corridor and outputs a 0–100 score — this run: Hormuz 40, Red Sea 80, Cape of Good Hope 20.",
  },
  {
    n: "02",
    title: "Model the disruption",
    desc: "Severity drives a full cascade: which suppliers lose volume, how much barrel capacity is lost, and what it does to price.",
  },
  {
    n: "03",
    title: "Rank the reroute",
    desc: "Alternative sources are ranked by real shipping lead-time, not a flat assumption, so the recommended fix is one you could actually execute.",
  },
];

export default function Home() {
  return (
    <div className="home" data-theme="dark">
      <div className="home__glow home__glow--1" />
      <div className="home__glow home__glow--2" />

      <nav className="home__nav">
        <Link to="/" className="home__brand">
          <ChokepointMark />
          <span>Chokepoint</span>
        </Link>
        <div className="home__nav-links">
          <a href="#pipeline">How it works</a>
          <a href="#capabilities">Capabilities</a>
          <Link to="/dashboard" className="home__nav-cta">Open dashboard</Link>
        </div>
      </nav>

      <header className="home__hero">
        <div className="home__hero-copy">
          <span className="home__eyebrow mono">SUPPLY CHAIN INTELLIGENCE · ENERGY SECURITY</span>
          <h1>
            Three sea lanes carry <em>India's crude.</em><br />
            We watch all three, live.
          </h1>
          <p>
            India imports roughly 88% of the crude it refines, and nearly half of that transits the
            Strait of Hormuz alone. Chokepoint turns geopolitical risk into a live disruption model —
            corridor by corridor, supplier by supplier — and ranks the reroute before a shortage
            reaches the refinery gate.
          </p>
          <div className="home__hero-actions">
            <Link to="/dashboard" className="home__btn home__btn--primary">
              Open live dashboard <span className="home__btn-arrow">→</span>
            </Link>
            <a href="#pipeline" className="home__btn home__btn--ghost">See how it works</a>
          </div>
        </div>

        <div className="home__hero-radar">
          <HeroRadar />
        </div>
      </header>

      <section className="home__stats">
        <Stat value="88%" label="of crude oil consumed is imported" />
        <Stat value="40–45%" label="of imports transit the Strait of Hormuz" />
        <Stat value="9.5 days" label="of national consumption held in strategic reserve" />
      </section>

      <section className="home__context">
        <p>
          The 2025 US–Iran standoff, renewed sanctions on Iranian exports, and repeated attacks on
          Red Sea shipping have each disrupted supply and pricing within the same year. Existing
          supply-chain planning tools weren't built to model geopolitical risk in real time, or to
          coordinate a rerouting response across refiners, logistics providers and reserves —
          Chokepoint is a first pass at closing that gap.
        </p>
      </section>

      <section className="home__pipeline" id="pipeline">
        <SectionHead
          eyebrow="How it works"
          title="From a risk score to an executable reroute"
          desc="Three stages, run continuously: this is the actual path data takes through the console."
        />
        <div className="home__pipeline-grid">
          {PIPELINE.map((p) => (
            <div className="pipeline-step" key={p.n}>
              <span className="pipeline-step__n mono">{p.n}</span>
              <h3>{p.title}</h3>
              <p>{p.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="home__capabilities" id="capabilities">
        <SectionHead
          eyebrow="Capability roadmap"
          title="Five agents, three shipped"
          desc="Illustrative directions from the problem brief, and where this build stands against each one."
        />
        <div className="home__capabilities-grid">
          {AGENTS.map((a) => (
            <div className="capability-card" key={a.title}>
              <div className="capability-card__icon">{a.icon}</div>
              <div className="capability-card__head">
                <h3>{a.title}</h3>
                <span className={`capability-card__status capability-card__status--${a.status}`}>
                  {a.status === "live" ? "Live in this build" : "Roadmap"}
                </span>
              </div>
              <p>{a.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="home__cta">
        <h2>The corridors are already scored. Go look.</h2>
        <Link to="/dashboard" className="home__btn home__btn--primary">
          Open live dashboard <span className="home__btn-arrow">→</span>
        </Link>
      </section>

      <footer className="home__footer">
        <div className="home__brand home__brand--footer">
          <ChokepointMark size={22} />
          <span>Chokepoint</span>
        </div>
        <span>Modelled estimates for planning discussion, not official forecasts. Built for Problem Statement 1 — AI-Driven Energy Supply Chain Resilience.</span>
      </footer>

      <style>{`
        .home {
          position: relative;
          min-height: 100%;
          background: var(--bg-deep);
          overflow: hidden;
        }
        .home__glow {
          position: absolute;
          border-radius: 50%;
          filter: blur(90px);
          pointer-events: none;
          z-index: 0;
        }
        .home__glow--1 {
          width: 560px; height: 560px;
          top: -180px; right: -120px;
          background: radial-gradient(circle, var(--accent-cyan-dim), transparent 70%);
        }
        .home__glow--2 {
          width: 460px; height: 460px;
          top: 40%; left: -160px;
          background: radial-gradient(circle, rgba(245,185,77,0.08), transparent 70%);
        }

        .home__nav, .home__hero, .home__stats, .home__context, .home__pipeline,
        .home__capabilities, .home__cta, .home__footer {
          position: relative;
          z-index: 1;
        }

        .home__nav {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 32px;
          position: sticky;
          top: 0;
          z-index: 30;
          backdrop-filter: blur(14px);
          background: linear-gradient(180deg, rgba(5,7,13,0.95), rgba(5,7,13,0.6));
          border-bottom: 1px solid var(--hairline);
        }
        .home__brand {
          display: flex;
          align-items: center;
          gap: 10px;
          font-family: var(--font-display);
          font-weight: 700;
          font-size: 17px;
          color: var(--text-primary) !important;
          text-decoration: none;
        }
        .home__brand--footer { font-size: 15px; }
        .home__nav-links {
          display: flex;
          align-items: center;
          gap: 30px;
          font-size: 13px;
          color: var(--text-secondary);
        }
        .home__nav-links > a:not(.home__nav-cta) {
          position: relative;
          text-decoration: none;
          color: var(--text-secondary);
          padding-bottom: 3px;
        }
        .home__nav-links > a:not(.home__nav-cta)::after {
          content: "";
          position: absolute;
          left: 0; bottom: 0;
          width: 0%; height: 1.5px;
          background: var(--accent-cyan);
          transition: width 0.25s ease;
        }
        .home__nav-links > a:not(.home__nav-cta):hover {
          color: var(--text-primary);
        }
        .home__nav-links > a:not(.home__nav-cta):hover::after {
          width: 100%;
        }
        .home__nav-cta {
          padding: 9px 18px;
          border-radius: 999px;
          border: 1px solid var(--accent-cyan);
          color: var(--text-primary) !important;
          background: var(--accent-cyan-dim);
          text-decoration: none;
          font-weight: 600;
          transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
        }
        .home__nav-cta:hover {
          background: var(--accent-cyan);
          color: var(--ink-900) !important;
          box-shadow: 0 0 24px var(--accent-cyan-dim);
          transform: translateY(-1px);
        }

        .home__hero {
          max-width: 1280px;
          margin: 0 auto;
          padding: 88px 32px 48px;
          display: grid;
          grid-template-columns: 1.05fr 0.95fr;
          gap: 48px;
          align-items: center;
        }
        .home__eyebrow {
          display: inline-block;
          font-size: 11px;
          letter-spacing: 0.14em;
          color: var(--accent-cyan);
          padding: 5px 12px;
          border: 1px solid var(--hairline-strong);
          border-radius: 999px;
          background: var(--ink-800);
        }
        .home__hero-copy h1 {
          font-family: var(--font-display);
          font-size: 48px;
          line-height: 1.15;
          margin: 20px 0 22px;
          letter-spacing: -0.015em;
          color: var(--text-primary);
        }
        .home__hero-copy h1 em {
          font-style: normal;
          color: var(--accent-cyan);
          text-shadow: 0 0 32px var(--accent-cyan-dim);
        }
        .home__hero-copy p {
          font-size: 15.5px;
          line-height: 1.7;
          color: var(--text-secondary);
          max-width: 520px;
          margin: 0 0 30px;
        }
        .home__hero-actions {
          display: flex;
          gap: 14px;
          flex-wrap: wrap;
        }
        .home__btn {
          font-family: var(--font-display);
          font-size: 13.5px;
          font-weight: 600;
          padding: 14px 24px;
          border-radius: var(--radius-sm);
          display: inline-flex;
          align-items: center;
          gap: 8px;
          text-decoration: none;
          transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        }
        .home__btn:hover { transform: translateY(-2px); }
        .home__btn-arrow { transition: transform 0.18s ease; }
        .home__btn:hover .home__btn-arrow { transform: translateX(3px); }
        .home__btn--primary {
          background: var(--accent-cyan);
          color: var(--ink-900) !important;
          box-shadow: 0 8px 28px var(--accent-cyan-dim);
        }
        .home__btn--primary:hover {
          box-shadow: 0 10px 36px rgba(55,201,224,0.35);
        }
        .home__btn--ghost {
          border: 1px solid var(--hairline-strong);
          color: var(--text-primary) !important;
          background: transparent;
        }
        .home__btn--ghost:hover { border-color: var(--accent-cyan); background: var(--ink-800); }

        .home__hero-radar {
          aspect-ratio: 1;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .home__stats {
          max-width: 1280px;
          margin: 0 auto;
          padding: 0 32px 64px;
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 20px;
        }

        .home__context {
          border-top: 1px solid var(--hairline);
          border-bottom: 1px solid var(--hairline);
          background: var(--ink-800);
        }
        .home__context p {
          max-width: 820px;
          margin: 0 auto;
          padding: 48px 32px;
          font-size: 16.5px;
          line-height: 1.8;
          color: var(--text-secondary);
          font-family: var(--font-display);
          font-weight: 500;
        }

        .home__pipeline, .home__capabilities {
          max-width: 1280px;
          margin: 0 auto;
          padding: 80px 32px;
        }

        .home__pipeline-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 24px;
          margin-top: 40px;
        }
        .pipeline-step {
          padding: 26px;
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          background: var(--ink-700);
          transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .pipeline-step:hover {
          transform: translateY(-3px);
          border-color: var(--accent-cyan);
          box-shadow: var(--shadow-card);
        }
        .pipeline-step__n {
          color: var(--accent-cyan);
          font-size: 22px;
          font-weight: 700;
          opacity: 0.6;
        }
        .pipeline-step h3 {
          font-family: var(--font-display);
          font-size: 16.5px;
          margin: 12px 0 8px;
          color: var(--text-primary);
        }
        .pipeline-step p {
          font-size: 13px;
          color: var(--text-secondary);
          line-height: 1.65;
          margin: 0;
        }

        .home__capabilities-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 20px;
          margin-top: 40px;
        }
        .capability-card {
          padding: 24px;
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          background: var(--ink-700);
          display: flex;
          flex-direction: column;
          gap: 14px;
          transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .capability-card:hover {
          transform: translateY(-3px);
          border-color: var(--hairline-strong);
        }
        .capability-card__icon {
          width: 36px;
          height: 36px;
          color: var(--accent-cyan);
        }
        .capability-card__head {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .capability-card__head h3 {
          font-family: var(--font-display);
          font-size: 14.5px;
          margin: 0;
          color: var(--text-primary);
        }
        .capability-card__status {
          align-self: flex-start;
          font-size: 10px;
          letter-spacing: 0.04em;
          padding: 3px 10px;
          border-radius: 999px;
          font-family: var(--font-mono);
        }
        .capability-card__status--live {
          color: var(--tier-safe);
          background: var(--tier-safe-dim);
        }
        .capability-card__status--roadmap {
          color: var(--text-muted);
          background: var(--ink-800);
          border: 1px solid var(--hairline);
        }
        .capability-card p {
          font-size: 12.5px;
          color: var(--text-secondary);
          line-height: 1.65;
          margin: 0;
        }

        .home__cta {
          text-align: center;
          padding: 90px 32px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 26px;
          background: radial-gradient(ellipse at center, var(--accent-cyan-dim), transparent 70%);
        }
        .home__cta h2 {
          font-family: var(--font-display);
          font-size: 28px;
          max-width: 520px;
          color: var(--text-primary);
        }

        .home__footer {
          border-top: 1px solid var(--hairline);
          padding: 28px 32px 40px;
          display: flex;
          flex-direction: column;
          gap: 10px;
          max-width: 1280px;
          margin: 0 auto;
        }
        .home__footer span {
          font-size: 11.5px;
          color: var(--text-muted);
          max-width: 640px;
        }

        @media (max-width: 900px) {
          .home__hero { grid-template-columns: 1fr; padding-top: 56px; }
          .home__hero-copy h1 { font-size: 36px; }
          .home__stats { grid-template-columns: 1fr; }
          .home__pipeline-grid, .home__capabilities-grid { grid-template-columns: 1fr; }
          .home__nav-links { gap: 16px; }
        }
      `}</style>
    </div>
  );
}

function Stat({ value, label }) {
  return (
    <div className="stat-block">
      <span className="stat-block__value mono">{value}</span>
      <span className="stat-block__label">{label}</span>
      <style>{`
        .stat-block {
          padding: 24px 26px;
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          background: var(--ink-700);
          display: flex;
          flex-direction: column;
          gap: 8px;
          transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .stat-block:hover {
          transform: translateY(-3px);
          border-color: var(--accent-cyan);
        }
        .stat-block__value {
          font-family: var(--font-display);
          font-size: 36px;
          font-weight: 700;
          color: var(--accent-cyan);
        }
        .stat-block__label {
          font-size: 12.5px;
          color: var(--text-secondary);
        }
      `}</style>
    </div>
  );
}

function SectionHead({ eyebrow, title, desc }) {
  return (
    <div className="section-head">
      <span className="mono section-head__eyebrow">{eyebrow.toUpperCase()}</span>
      <h2>{title}</h2>
      <p>{desc}</p>
      <style>{`
        .section-head__eyebrow {
          font-size: 10.5px;
          letter-spacing: 0.1em;
          color: var(--accent-cyan);
        }
        .section-head h2 {
          font-family: var(--font-display);
          font-size: 28px;
          margin: 12px 0 8px;
          color: var(--text-primary);
        }
        .section-head p {
          font-size: 13.5px;
          color: var(--text-secondary);
          max-width: 560px;
          line-height: 1.65;
        }
      `}</style>
    </div>
  );
}

function HeroRadar() {
  const corridors = sampleData.phase1_risk_report;
  const nodes = [
    { key: "strait_of_hormuz", angle: -35, r: 92 },
    { key: "red_sea", angle: -150, r: 108 },
    { key: "cape_of_good_hope", angle: 200, r: 130 },
  ];
  const size = 420;
  const c = size / 2;

  return (
    <svg width="100%" viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Live corridor risk radar">
      <defs>
        <radialGradient id="hero-ping" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity="0.55" />
          <stop offset="100%" stopColor="var(--accent-cyan)" stopOpacity="0" />
        </radialGradient>
      </defs>
      {[70, 110, 150, 190].map((r) => (
        <circle key={r} cx={c} cy={c} r={r} fill="none" stroke="var(--hairline)" strokeWidth="1" />
      ))}
      <g style={{ transformOrigin: `${c}px ${c}px` }} className="hero-radar__sweep">
        <path d={`M ${c} ${c} L ${c + 190} ${c} A 190 190 0 0 0 ${c + 134} ${c - 134} Z`} fill="var(--accent-cyan)" opacity="0.07" />
      </g>
      {nodes.map(({ key, angle, r }) => {
        const risk = corridors[key];
        const tier = tierForSeverity(risk.risk_score / 100);
        const color = `var(${TIER_COLOR_VAR[tier]})`;
        const rad = (angle * Math.PI) / 180;
        const x = c + r * Math.cos(rad);
        const y = c + r * Math.sin(rad);
        return (
          <g key={key} transform={`translate(${x}, ${y})`}>
            <line x1={c - x} y1={c - y} x2="0" y2="0" stroke={color} strokeWidth="1.2" strokeDasharray="4 4" opacity="0.5" />
            <circle r="14" fill="url(#hero-ping)" className="hero-radar__ping" />
            <circle r="5" fill={color} stroke="var(--ink-900)" strokeWidth="1.5" />
            <text y="-20" textAnchor="middle" className="hero-radar__label mono">{risk.name}</text>
            <text y="-8" textAnchor="middle" className="hero-radar__score mono" style={{ fill: color }}>{risk.risk_score}</text>
          </g>
        );
      })}
      <circle cx={c} cy={c} r="16" fill="url(#hero-ping)" className="hero-radar__ping" />
      <circle cx={c} cy={c} r="7" fill="var(--accent-amber)" stroke="var(--ink-900)" strokeWidth="1.5" />
      <text x={c} y={c + 24} textAnchor="middle" className="hero-radar__label mono">INDIA</text>
      <style>{`
        .hero-radar__ping { animation: hero-ping 2.6s ease-out infinite; transform-origin: center; }
        .hero-radar__sweep { animation: hero-sweep 7s linear infinite; }
        .hero-radar__label { font-size: 10px; fill: var(--text-muted); letter-spacing: 0.04em; }
        .hero-radar__score { font-size: 13px; font-weight: 700; }
        @keyframes hero-ping {
          0% { transform: scale(0.4); opacity: 0.9; }
          100% { transform: scale(2); opacity: 0; }
        }
        @keyframes hero-sweep {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </svg>
  );
}

function IconRadar() {
  return (
    <svg viewBox="0 0 34 34" fill="none">
      <circle cx="17" cy="17" r="14" stroke="currentColor" strokeWidth="1.4" opacity="0.4" />
      <circle cx="17" cy="17" r="8" stroke="currentColor" strokeWidth="1.4" opacity="0.6" />
      <circle cx="17" cy="17" r="2.2" fill="currentColor" />
      <path d="M17 17 L28 8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}
function IconWave() {
  return (
    <svg viewBox="0 0 34 34" fill="none">
      <path d="M4 20 Q 9 10, 14 20 T 24 20 T 34 20" stroke="currentColor" strokeWidth="1.6" fill="none" />
      <path d="M4 26 Q 9 18, 14 26 T 24 26 T 34 26" stroke="currentColor" strokeWidth="1.2" opacity="0.5" fill="none" />
    </svg>
  );
}
function IconGlobe() {
  return (
    <svg viewBox="0 0 34 34" fill="none">
      <circle cx="17" cy="17" r="13" stroke="currentColor" strokeWidth="1.4" />
      <ellipse cx="17" cy="17" rx="13" ry="5.5" stroke="currentColor" strokeWidth="1.2" opacity="0.6" />
      <path d="M17 4 V30" stroke="currentColor" strokeWidth="1.2" opacity="0.6" />
    </svg>
  );
}
function IconRoute() {
  return (
    <svg viewBox="0 0 34 34" fill="none">
      <circle cx="6" cy="26" r="2.6" fill="currentColor" />
      <circle cx="28" cy="8" r="2.6" fill="currentColor" />
      <path d="M6 26 C 16 26, 12 10, 28 8" stroke="currentColor" strokeWidth="1.4" strokeDasharray="3 4" fill="none" />
    </svg>
  );
}
function IconGauge() {
  return (
    <svg viewBox="0 0 34 34" fill="none">
      <path d="M5 24 A 12 12 0 0 1 29 24" stroke="currentColor" strokeWidth="1.6" fill="none" />
      <path d="M17 24 L 23 14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <circle cx="17" cy="24" r="1.8" fill="currentColor" />
    </svg>
  );
}