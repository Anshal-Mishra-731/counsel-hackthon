import { Link } from "react-router-dom";
import { ChokepointMark } from "../components/Header";
import { RISK_COLORS } from "../lib/api";

const FEATURES = [
  {
    title: "Live risk radar",
    desc: "Phase-1 geopolitical risk scoring per corridor, refreshed on a timer from live news signals.",
    icon: <IconRadar />,
    color: "#37c9e0",
    big: true,
  },
  {
    title: "Route simulator",
    desc: "Pick any source and destination — the map draws every plausible sea route, colored by live risk.",
    icon: <IconRoute />,
    color: "#f5b94d",
  },
  {
    title: "Full route intel",
    desc: "Click a route's floating buoy for affected suppliers, alternate sources and replacement timelines.",
    icon: <IconLayers />,
    color: "#fb7185",
  },
  {
    title: "Dataset-driven analytics",
    desc: "Corridor dependency, supplier breakdown and baseline demand — charted straight from your CSVs.",
    icon: <IconChart />,
    color: "#34d399",
  },
  {
    title: "Light & dark",
    desc: "One toggle, every screen — built for a war-room projector or a laptop at 2am.",
    icon: <IconMoon />,
    color: "#a78bfa",
  },
  {
    title: "Full-screen map",
    desc: "One click drops the map into full screen for a presentation-ready view.",
    icon: <IconExpand />,
    color: "#37c9e0",
  },
];

const STEPS = [
  { n: "01", title: "Choose a corridor", desc: "Search or click a supplier country — the destination is fixed to India's refinery ports." },
  { n: "02", title: "Read the risk", desc: "Every route is colored live: green for calm waters, red for corridors under active threat." },
  { n: "03", title: "Open the breakdown", desc: "Tap a route's buoy for the full disruption model — suppliers, alternates, timelines, price impact." },
];

const CORRIDORS_TICKER = [
  { name: "Strait of Hormuz", score: 40, bucket: "elevated" },
  { name: "Suez Canal / Red Sea", score: 80, bucket: "critical" },
  { name: "Cape of Good Hope", score: 20, bucket: "low" },
  { name: "Strait of Malacca", score: 18, bucket: "low" },
  { name: "INSTC", score: 15, bucket: "low" },
  { name: "Chennai–Vladivostok", score: 12, bucket: "low" },
];

export default function Home({ theme, setTheme }) {
  return (
    <div className="home" data-theme={theme}>

      {/* ================= NAVBAR ================= */}
      <nav className="home__nav">
        <Link to="/" className="home__brand">
          <ChokepointMark />
          <span>Counsel</span>
        </Link>
        <div className="home__nav-links">
          <a href="#features">Features</a>
          <a href="#how">How it works</a>
          <div className="theme-toggle">
            <button className={theme === "dark" ? "active" : ""} onClick={() => setTheme("dark")}>🌙</button>
            <button className={theme === "light" ? "active" : ""} onClick={() => setTheme("light")}>☀️</button>
          </div>
          <Link to="/dashboard" className="home__nav-cta">
            Open dashboard <span className="home__nav-cta-arrow">→</span>
          </Link>
        </div>
      </nav>

      {/* ================= HERO ================= */}
      <header className="home__hero">
        <div className="home__hero-copy">
          <span className="home__eyebrow mono">
            <span className="home__eyebrow-dot" /> LIVE · SUPPLY CHAIN INTELLIGENCE
          </span>
          <h1>
            Pick two countries.<br />
            <span className="home__gradient-text">See the risk between them.</span>
          </h1>
          <p>
            Chokepoint turns geopolitical risk into a live sea-route simulator — search or click a
            source and destination, see every plausible route colored by risk, and open any route
            for the full breakdown: affected suppliers, alternate sources and how fast they could
            cover the gap.
          </p>
          <div className="home__actions">
            <Link to="/dashboard" className="home__btn home__btn--primary">
              Open live dashboard <span className="home__btn-arrow">→</span>
            </Link>
            <a href="#features" className="home__btn home__btn--ghost">See what's inside</a>
          </div>

          <div className="home__trust">
            <TrustItem label="Built on live news scoring" />
            <TrustItem label="Real CSV-derived supplier data" />
            <TrustItem label="Shipping-lane accurate lead times" />
          </div>
        </div>

        <div className="home__hero-visual">
          <div className="home__hero-visual-glow" />
          <MockDashboard />
          <div className="floating-chip floating-chip--1">
            <span className="floating-chip__dot" style={{ background: RISK_COLORS.critical }} />
            Red Sea · risk 80
          </div>
          <div className="floating-chip floating-chip--2">
            <span className="floating-chip__dot" style={{ background: RISK_COLORS.low }} />
            +5 alt. suppliers found
          </div>
        </div>
      </header>

      {/* ================= LIVE TICKER ================= */}
      <div className="home__ticker-wrap">
        <div className="home__ticker">
          {[...CORRIDORS_TICKER, ...CORRIDORS_TICKER].map((c, i) => (
            <span className="ticker-item" key={i}>
              <span className="ticker-dot" style={{ background: RISK_COLORS[c.bucket] }} />
              {c.name}
              <span className="ticker-score mono" style={{ color: RISK_COLORS[c.bucket] }}>{c.score}</span>
            </span>
          ))}
        </div>
      </div>

      {/* ================= STATS ================= */}
      <section className="home__stats">
        <div className="home__stat">
          <div className="val mono">88%</div>
          <div className="lbl">of India's crude oil is imported</div>
        </div>
        <div className="home__stat">
          <div className="val mono">40–45%</div>
          <div className="lbl">transits the Strait of Hormuz</div>
        </div>
        <div className="home__stat">
          <div className="val mono">9.5 days</div>
          <div className="lbl">of consumption held in reserve</div>
        </div>
        <div className="home__stat home__stat--accent">
          <div className="val mono">6</div>
          <div className="lbl">corridors monitored, live</div>
        </div>
      </section>

      {/* ================= HOW IT WORKS ================= */}
      <section className="home__steps" id="how">
        <SectionHead
          eyebrow="How it works"
          title="From a click to a full disruption model"
          desc="Three steps, running continuously behind the scenes."
        />
        <div className="home__steps-grid">
          {STEPS.map((s, i) => (
            <div className="step-card" key={s.n}>
              <span className="step-card__n mono">{s.n}</span>
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
              {i < STEPS.length - 1 && <span className="step-card__connector">→</span>}
            </div>
          ))}
        </div>
      </section>

      {/* ================= FEATURES (bento) ================= */}
      <section className="home__features-wrap" id="features">
        <SectionHead
          eyebrow="Inside the console"
          title="Everything a war room actually needs"
          desc="Not a slide deck — a working console you can point at a live incident."
        />
        <div className="home__features">
          {FEATURES.map((f) => (
            <div className={`feature-card ${f.big ? "feature-card--big" : ""}`} key={f.title} style={{ "--card-accent": f.color }}>
              <div className="feature-card__icon" style={{ background: `${f.color}1a`, color: f.color }}>
                {f.icon}
              </div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ================= CTA ================= */}
      <section className="home__cta">
        <div className="home__cta-glow" />
        <span className="home__eyebrow mono home__eyebrow--center">READY WHEN YOU ARE</span>
        <h2>The corridors are already scored.<br />Go look.</h2>
        <Link to="/dashboard" className="home__btn home__btn--primary home__btn--lg">
          Open live dashboard <span className="home__btn-arrow">→</span>
        </Link>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="home__footer">
        <div className="home__footer-top">
          <div className="home__footer-brand">
            <div className="home__brand">
              <ChokepointMark size={26} />
              <span>Chokepoint</span>
            </div>
            <p>
              Live maritime corridor risk intelligence for India's crude oil supply chain.
              Modelled estimates for planning discussion — not an official forecast.
            </p>
            <div className="home__footer-status">
              <span className="status-dot status-dot--live" /> Live scoring active
            </div>
          </div>

          <div className="home__footer-col">
            <h4>Product</h4>
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
            <Link to="/dashboard">Live dashboard</Link>
          </div>

          <div className="home__footer-col">
            <h4>Corridors monitored</h4>
            <span>Strait of Hormuz</span>
            <span>Suez Canal / Red Sea</span>
            <span>Cape of Good Hope</span>
            <span>Strait of Malacca</span>
          </div>

          <div className="home__footer-col">
            <h4>Built for</h4>
            <span>Problem Statement 1</span>
            <span>AI-Driven Energy</span>
            <span>Supply Chain Resilience</span>
          </div>
        </div>

        <div className="home__footer-bottom">
          <span>© {new Date().getFullYear()} Chokepoint. All data modelled for planning purposes.</span>
        </div>
      </footer>

      <style>{`
        .home {
          position: relative;
          min-height: 100%;
          background: var(--bg-deep);
          overflow: hidden;
          color: var(--text-primary);
        }
        .home__grid-bg {
          position: absolute;
          inset: 0;
          background-image:
            linear-gradient(var(--hairline) 1px, transparent 1px),
            linear-gradient(90deg, var(--hairline) 1px, transparent 1px);
          background-size: 64px 64px;
          mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, black 20%, transparent 75%);
          opacity: 0.5;
          pointer-events: none;
          z-index: 0;
        }
        .home__glow {
          position: absolute;
          border-radius: 50%;
          filter: blur(110px);
          pointer-events: none;
          z-index: 0;
        }
        .home__glow--1 {
          width: 620px; height: 620px;
          top: -240px; right: -150px;
          background: radial-gradient(circle, var(--accent-cyan-dim), transparent 70%);
        }
        .home__glow--2 {
          width: 500px; height: 500px;
          top: 60%; left: -190px;
          background: radial-gradient(circle, rgba(245,185,77,0.09), transparent 70%);
        }
        .home > * { position: relative; z-index: 1; }

        /* NAV */
        .home__nav {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 18px 32px;
          position: sticky;
          top: 0;
          z-index: 40;
          backdrop-filter: blur(16px);
          background: linear-gradient(180deg, rgba(5,7,13,0.9), rgba(5,7,13,0.55));
          border-bottom: 1px solid var(--hairline);
        }
        .home__brand {
          display: flex; align-items: center; gap: 10px;
          font-family: var(--font-display); font-weight: 700; font-size: 17px;
          color: var(--text-primary) !important; text-decoration: none;
        }
        .home__nav-links { display: flex; align-items: center; gap: 26px; font-size: 13px; color: var(--text-secondary); }
        .home__nav-links > a { position: relative; text-decoration: none; color: var(--text-secondary); padding-bottom: 3px; }
        .home__nav-links > a::after {
          content: ""; position: absolute; left: 0; bottom: 0; width: 0%; height: 1.5px;
          background: var(--accent-cyan); transition: width 0.25s ease;
        }
        .home__nav-links > a:hover { color: var(--text-primary); }
        .home__nav-links > a:hover::after { width: 100%; }
        .theme-toggle { display: flex; gap: 4px; background: var(--ink-700); border-radius: 999px; padding: 3px; }
        .theme-toggle button { all: unset; cursor: pointer; padding: 5px 9px; border-radius: 999px; font-size: 13px; }
        .theme-toggle button.active { background: var(--accent-cyan-dim); }
        .home__nav-cta {
          display: inline-flex; align-items: center; gap: 6px;
          padding: 9px 18px; border-radius: 999px; border: 1px solid var(--accent-cyan);
          color: var(--text-primary) !important; background: var(--accent-cyan-dim);
          text-decoration: none; font-weight: 600;
          transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
        }
        .home__nav-cta-arrow { transition: transform 0.2s ease; }
        .home__nav-cta:hover { background: var(--accent-cyan); color: var(--ink-900) !important; box-shadow: 0 0 24px var(--accent-cyan-dim); transform: translateY(-1px); }
        .home__nav-cta:hover .home__nav-cta-arrow { transform: translateX(3px); }

        /* HERO */
        .home__hero {
          max-width: 1320px; margin: 0 auto; padding: 90px 32px 64px;
          display: grid; grid-template-columns: 1.05fr 0.95fr; gap: 56px; align-items: center;
        }
        .home__eyebrow {
          display: inline-flex; align-items: center; gap: 8px;
          font-size: 11px; letter-spacing: 0.12em; color: var(--accent-cyan);
          padding: 6px 14px; border: 1px solid var(--hairline-strong); border-radius: 999px; background: var(--ink-800);
        }
        .home__eyebrow--center { margin-bottom: -6px; }
        .home__eyebrow-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--tier-safe); animation: pulse 2s infinite; }
        @keyframes pulse { 0%{box-shadow:0 0 0 0 var(--tier-safe-dim);}70%{box-shadow:0 0 0 8px transparent;}100%{box-shadow:0 0 0 0 transparent;} }
        .home__hero-copy h1 {
          font-family: var(--font-display); font-size: 54px; line-height: 1.1; margin: 22px 0 24px;
          letter-spacing: -0.02em; color: var(--text-primary);
        }
        .home__gradient-text {
          background: linear-gradient(90deg, var(--accent-cyan), #6ee7ff 60%, var(--accent-cyan));
          -webkit-background-clip: text; background-clip: text; color: transparent;
          filter: drop-shadow(0 0 24px var(--accent-cyan-dim));
        }
        .home__hero-copy p { font-size: 16px; line-height: 1.72; color: var(--text-secondary); max-width: 540px; margin: 0 0 28px; }
        .home__actions { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 24px; }
        .home__btn {
          font-family: var(--font-display); font-size: 13.5px; font-weight: 600; padding: 14px 24px;
          border-radius: var(--radius-sm); display: inline-flex; align-items: center; gap: 8px; text-decoration: none;
          transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        }
        .home__btn:hover { transform: translateY(-2px); }
        .home__btn-arrow { transition: transform 0.18s ease; }
        .home__btn:hover .home__btn-arrow { transform: translateX(3px); }
        .home__btn--primary { background: var(--accent-cyan); color: var(--ink-900) !important; box-shadow: 0 8px 30px var(--accent-cyan-dim); }
        .home__btn--primary:hover { box-shadow: 0 12px 40px rgba(55,201,224,0.4); }
        .home__btn--ghost { border: 1px solid var(--hairline-strong); color: var(--text-primary) !important; background: transparent; }
        .home__btn--ghost:hover { border-color: var(--accent-cyan); background: var(--ink-800); }
        .home__btn--lg { padding: 17px 32px; font-size: 15px; }

        .home__trust { display: flex; flex-direction: column; gap: 8px; }
        .trust-item { display: flex; align-items: center; gap: 8px; font-size: 12.5px; color: var(--text-muted); font-family: var(--font-mono); }
        .trust-item__check { color: var(--tier-safe); font-size: 13px; }

        /* HERO VISUAL */
        .home__hero-visual { position: relative; display: flex; align-items: center; justify-content: center; }
        .home__hero-visual-glow {
          position: absolute; width: 380px; height: 380px; border-radius: 50%;
          background: radial-gradient(circle, var(--accent-cyan-dim), transparent 70%); filter: blur(30px); z-index: -1;
        }
        .mock-dash {
          width: 100%; max-width: 460px; border-radius: var(--radius-lg);
          background: var(--ink-800); border: 1px solid var(--hairline-strong);
          box-shadow: 0 30px 90px rgba(0,0,0,0.55); overflow: hidden;
          transform: perspective(1200px) rotateY(-6deg) rotateX(2deg);
          animation: float 6s ease-in-out infinite;
        }
        @keyframes float { 0%,100% { transform: perspective(1200px) rotateY(-6deg) rotateX(2deg) translateY(0); } 50% { transform: perspective(1200px) rotateY(-6deg) rotateX(2deg) translateY(-10px); } }
        .mock-dash__bar { display: flex; gap: 6px; padding: 10px 14px; border-bottom: 1px solid var(--hairline); }
        .mock-dash__dot { width: 9px; height: 9px; border-radius: 50%; background: var(--hairline-strong); }
        .mock-dash__body { padding: 18px; display: flex; flex-direction: column; gap: 12px; }
        .mock-dash__row { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; border-radius: var(--radius-sm); background: var(--ink-700); border: 1px solid var(--hairline); }
        .mock-dash__row-name { font-size: 12px; color: var(--text-secondary); }
        .mock-dash__row-score { font-family: var(--font-mono); font-size: 11.5px; font-weight: 700; padding: 2px 9px; border-radius: 999px; color: #0a0f1c; }
        .mock-dash__map { height: 140px; border-radius: var(--radius-sm); background: var(--ink-900); position: relative; overflow: hidden; margin-top: 4px; }
        .mock-dash__map-line { position: absolute; height: 2.5px; border-radius: 2px; }
        .mock-dash__map-dot { position: absolute; width: 11px; height: 11px; border-radius: 50%; border: 2px solid var(--ink-900); box-shadow: 0 0 0 3px rgba(45,212,191,0.25); }

        .floating-chip {
          position: absolute; display: flex; align-items: center; gap: 7px;
          padding: 9px 14px; border-radius: 999px; background: var(--ink-800);
          border: 1px solid var(--hairline-strong); font-size: 11.5px; font-family: var(--font-mono);
          box-shadow: var(--shadow-card); animation: float2 5s ease-in-out infinite;
        }
        .floating-chip__dot { width: 7px; height: 7px; border-radius: 50%; }
        .floating-chip--1 { top: 8%; right: -4%; animation-delay: 0.4s; }
        .floating-chip--2 { bottom: 10%; left: -6%; animation-delay: 1.2s; }
        @keyframes float2 { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }

        /* TICKER */
        .home__ticker-wrap {
          border-top: 1px solid var(--hairline); border-bottom: 1px solid var(--hairline);
          background: var(--ink-800); overflow: hidden; padding: 14px 0;
        }
        .home__ticker { display: flex; gap: 40px; width: max-content; animation: ticker 24s linear infinite; }
        .home__ticker-wrap:hover .home__ticker { animation-play-state: paused; }
        @keyframes ticker { from { transform: translateX(0); } to { transform: translateX(-50%); } }
        .ticker-item { display: flex; align-items: center; gap: 8px; font-size: 12.5px; color: var(--text-secondary); white-space: nowrap; }
        .ticker-dot { width: 6px; height: 6px; border-radius: 50%; }
        .ticker-score { font-weight: 700; }

        /* STATS */
        .home__stats {
          max-width: 1320px; margin: 0 auto; padding: 56px 32px 64px;
          display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px;
        }
        .home__stat {
          padding: 24px; border: 1px solid var(--hairline); border-radius: var(--radius-lg);
          background: var(--ink-700); display: flex; flex-direction: column; gap: 6px;
          transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .home__stat:hover { transform: translateY(-4px); border-color: var(--accent-cyan); box-shadow: 0 12px 30px var(--accent-cyan-dim); }
        .home__stat--accent { background: linear-gradient(135deg, var(--accent-cyan-dim), var(--ink-700)); border-color: var(--accent-cyan); }
        .home__stat .val { font-family: var(--font-display); font-size: 32px; font-weight: 700; color: var(--accent-cyan); }
        .home__stat .lbl { font-size: 12px; color: var(--text-secondary); }

        /* STEPS */
        .home__steps { max-width: 1320px; margin: 0 auto; padding: 64px 32px; }
        .home__steps-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; margin-top: 40px; }
        .step-card {
          padding: 28px; border: 1px solid var(--hairline); border-radius: var(--radius-lg); background: var(--ink-700);
          transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease; position: relative;
        }
        .step-card:hover { transform: translateY(-4px); border-color: var(--accent-cyan); box-shadow: 0 16px 40px rgba(0,0,0,0.3); }
        .step-card__n {
          display: inline-flex; align-items: center; justify-content: center;
          width: 40px; height: 40px; border-radius: 50%; background: var(--accent-cyan-dim);
          color: var(--accent-cyan); font-size: 15px; font-weight: 700;
        }
        .step-card h3 { font-family: var(--font-display); font-size: 17px; margin: 16px 0 8px; color: var(--text-primary); }
        .step-card p { font-size: 13px; color: var(--text-secondary); line-height: 1.65; margin: 0; }
        .step-card__connector {
          display: none;
        }
        @media (min-width: 981px) {
          .step-card:not(:last-child)::after {
            content: "→"; position: absolute; right: -28px; top: 50%; transform: translateY(-50%);
            color: var(--hairline-strong); font-size: 18px;
          }
        }

        /* FEATURES BENTO */
        .home__features-wrap { max-width: 1320px; margin: 0 auto; padding: 64px 32px 90px; }
        .home__features {
          display: grid; grid-template-columns: repeat(3, 1fr); grid-auto-rows: 1fr; gap: 18px; margin-top: 40px;
        }
        .feature-card {
          padding: 28px; border: 1px solid var(--hairline); border-radius: var(--radius-lg); background: var(--ink-700);
          display: flex; flex-direction: column; gap: 14px; position: relative; overflow: hidden;
          transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
        }
        .feature-card::before {
          content: ""; position: absolute; inset: 0; opacity: 0; transition: opacity 0.25s ease;
          background: radial-gradient(220px circle at 20% 0%, color-mix(in srgb, var(--card-accent) 12%, transparent), transparent 70%);
        }
        .feature-card:hover { transform: translateY(-4px); border-color: color-mix(in srgb, var(--card-accent) 45%, var(--hairline-strong)); box-shadow: 0 18px 44px rgba(0,0,0,0.32); }
        .feature-card:hover::before { opacity: 1; }
        .feature-card--big { grid-column: span 2; }
        .feature-card__icon {
          width: 44px; height: 44px; border-radius: 12px;
          display: flex; align-items: center; justify-content: center;
        }
        .feature-card__icon svg { width: 22px; height: 22px; }
        .feature-card h3 { font-family: var(--font-display); font-size: 15.5px; margin: 0; color: var(--text-primary); position: relative; }
        .feature-card p { font-size: 12.5px; color: var(--text-secondary); line-height: 1.65; margin: 0; position: relative; }

        /* CTA */
        .home__cta {
          position: relative; text-align: center; padding: 100px 32px;
          display: flex; flex-direction: column; align-items: center; gap: 22px; overflow: hidden;
        }
        .home__cta-glow {
          position: absolute; inset: 0; background: radial-gradient(ellipse 500px 300px at center, var(--accent-cyan-dim), transparent 70%); z-index: -1;
        }
        .home__cta h2 { font-family: var(--font-display); font-size: 32px; line-height: 1.28; max-width: 580px; color: var(--text-primary); margin: 0; }

        /* FOOTER */
        .home__footer { border-top: 1px solid var(--hairline); background: var(--ink-800); padding: 60px 32px 30px; }
        .home__footer-top {
          max-width: 1320px; margin: 0 auto 40px;
          display: grid; grid-template-columns: 1.6fr 1fr 1fr 1fr; gap: 40px;
        }
        .home__footer-brand p { font-size: 12.5px; color: var(--text-muted); line-height: 1.65; margin: 14px 0; max-width: 320px; }
        .home__footer-col { display: flex; flex-direction: column; gap: 11px; }
        .home__footer-col h4 { font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted); margin: 0 0 6px; }
        .home__footer-col a, .home__footer-col span { font-size: 12.5px; color: var(--text-secondary); text-decoration: none; }
        .home__footer-col a:hover { color: var(--accent-cyan); }
        .home__footer-bottom {
          max-width: 1320px; margin: 0 auto; padding-top: 26px; border-top: 1px solid var(--hairline);
          font-size: 11.5px; color: var(--text-muted);
        }
        .home__footer-status { display: flex; align-items: center; gap: 6px; font-size: 11.5px; color: var(--text-muted); }
        .status-dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
        .status-dot--live { background: var(--tier-safe); animation: pulse 2s infinite; }

        @media (max-width: 980px) {
          .home__hero { grid-template-columns: 1fr; padding-top: 64px; }
          .home__hero-copy h1 { font-size: 38px; }
          .floating-chip { display: none; }
          .home__stats { grid-template-columns: repeat(2, 1fr); }
          .home__steps-grid, .home__features { grid-template-columns: 1fr; }
          .feature-card--big { grid-column: span 1; }
          .step-card::after { display: none; }
          .home__footer-top { grid-template-columns: 1fr 1fr; }
          .home__nav-links { gap: 14px; }
        }
      `}</style>
    </div>
  );
}

function TrustItem({ label }) {
  return (
    <div className="trust-item">
      <span className="trust-item__check">✓</span> {label}
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
        .section-head__eyebrow { font-size: 10.5px; letter-spacing: 0.1em; color: var(--accent-cyan); }
        .section-head h2 { font-family: var(--font-display); font-size: 30px; margin: 12px 0 8px; color: var(--text-primary); }
        .section-head p { font-size: 13.5px; color: var(--text-secondary); max-width: 560px; line-height: 1.65; }
      `}</style>
    </div>
  );
}

function MockDashboard() {
  const rows = [
    { name: "Strait of Hormuz", score: 40, color: RISK_COLORS.elevated },
    { name: "Red Sea", score: 80, color: RISK_COLORS.critical },
    { name: "Cape of Good Hope", score: 20, color: RISK_COLORS.low },
  ];
  return (
    <div className="mock-dash">
      <div className="mock-dash__bar">
        <span className="mock-dash__dot" />
        <span className="mock-dash__dot" />
        <span className="mock-dash__dot" />
      </div>
      <div className="mock-dash__body">
        {rows.map((r) => (
          <div className="mock-dash__row" key={r.name}>
            <span className="mock-dash__row-name">{r.name}</span>
            <span className="mock-dash__row-score" style={{ background: r.color }}>{r.score}</span>
          </div>
        ))}
        <div className="mock-dash__map">
          <div className="mock-dash__map-line" style={{ top: "28%", left: "8%", width: "48%", background: RISK_COLORS.elevated, transform: "rotate(9deg)" }} />
          <div className="mock-dash__map-line" style={{ top: "58%", left: "18%", width: "58%", background: RISK_COLORS.critical, transform: "rotate(-7deg)" }} />
          <div className="mock-dash__map-line" style={{ top: "82%", left: "4%", width: "72%", background: RISK_COLORS.low, transform: "rotate(3deg)" }} />
          <div className="mock-dash__map-dot" style={{ top: "68%", left: "78%", background: "#2dd4bf" }} />
        </div>
      </div>
    </div>
  );
}

function IconRadar() {
  return (
    <svg viewBox="0 0 34 34" fill="none">
      <circle cx="17" cy="17" r="14" stroke="currentColor" strokeWidth="1.6" opacity="0.4" />
      <circle cx="17" cy="17" r="8" stroke="currentColor" strokeWidth="1.6" opacity="0.65" />
      <circle cx="17" cy="17" r="2.4" fill="currentColor" />
      <path d="M17 17 L28 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}
function IconRoute() {
  return (
    <svg viewBox="0 0 34 34" fill="none">
      <circle cx="6" cy="26" r="2.8" fill="currentColor" />
      <circle cx="28" cy="8" r="2.8" fill="currentColor" />
      <path d="M6 26 C 16 26, 12 10, 28 8" stroke="currentColor" strokeWidth="1.6" strokeDasharray="3 4" fill="none" />
    </svg>
  );
}
function IconLayers() {
  return (
    <svg viewBox="0 0 34 34" fill="none">
      <path d="M17 4 L30 12 L17 20 L4 12 Z" stroke="currentColor" strokeWidth="1.6" fill="none" />
      <path d="M4 20 L17 28 L30 20" stroke="currentColor" strokeWidth="1.6" fill="none" opacity="0.65" />
    </svg>
  );
}
function IconChart() {
  return (
    <svg viewBox="0 0 34 34" fill="none">
      <path d="M5 28 V6" stroke="currentColor" strokeWidth="1.6" />
      <path d="M5 28 H30" stroke="currentColor" strokeWidth="1.6" />
      <rect x="9" y="18" width="4" height="10" fill="currentColor" opacity="0.65" />
      <rect x="16" y="12" width="4" height="16" fill="currentColor" opacity="0.85" />
      <rect x="23" y="8" width="4" height="20" fill="currentColor" />
    </svg>
  );
}
function IconMoon() {
  return (
    <svg viewBox="0 0 34 34" fill="none">
      <path d="M24 20 A11 11 0 1 1 14 6 A9 9 0 0 0 24 20 Z" stroke="currentColor" strokeWidth="1.6" fill="none" />
    </svg>
  );
}
function IconExpand() {
  return (
    <svg viewBox="0 0 34 34" fill="none">
      <path d="M6 12 V6 H12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" fill="none" />
      <path d="M22 6 H28 V12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" fill="none" />
      <path d="M28 22 V28 H22" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" fill="none" />
      <path d="M12 28 H6 V22" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" fill="none" />
    </svg>
  );
}