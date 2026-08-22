import { Link } from "react-router-dom";
import { ChokepointMark } from "../components/Header";

const FEATURES = [
  { title: "Live risk radar", desc: "Phase-1 geopolitical risk scoring per corridor, refreshed on a timer from live news signals." },
  { title: "Route simulator", desc: "Pick any source and destination — the map draws every plausible sea route, colored by live risk." },
  { title: "Full route intel", desc: "Click a route's floating buoy for affected suppliers, alternate sources and replacement timelines." },
  { title: "Dataset-driven analytics", desc: "Corridor dependency, supplier breakdown and baseline demand — charted straight from your CSVs." },
  { title: "Light & dark", desc: "One toggle, every screen — built for a war-room projector or a laptop at 2am." },
  { title: "Full-screen map", desc: "One click drops the map into full screen for a presentation-ready view." },
];

export default function Home({ theme, setTheme }) {
  return (
    <div className="home">
      <nav className="home__nav">
        <Link to="/" className="home__brand">
          <ChokepointMark />
          <span>Chokepoint</span>
        </Link>
        <div className="home__nav-links">
          <a href="#features">Features</a>
          <div className="theme-toggle" style={{ display: "inline-flex" }}>
            <button className={theme === "dark" ? "active" : ""} onClick={() => setTheme("dark")}>🌙</button>
            <button className={theme === "light" ? "active" : ""} onClick={() => setTheme("light")}>☀️</button>
          </div>
          <Link to="/dashboard" className="home__nav-cta">Open dashboard</Link>
        </div>
      </nav>

      <header className="home__hero">
        <div>
          <span className="home__eyebrow mono">SUPPLY CHAIN INTELLIGENCE · ENERGY SECURITY</span>
          <h1>
            Pick two countries.<br /><em>See the risk between them.</em>
          </h1>
          <p>
            Chokepoint turns geopolitical risk into a live sea-route simulator — search or click a
            source and destination, see every plausible route colored by risk, and open any route
            for the full breakdown: affected suppliers, alternate sources and how fast they could
            cover the gap.
          </p>
          <div className="home__actions">
            <Link to="/dashboard" className="home__btn home__btn--primary">Open live dashboard</Link>
            <a href="#features" className="home__btn home__btn--ghost">See what's inside</a>
          </div>
        </div>
      </header>

      <section className="home__stats">
        <div className="home__stat"><div className="val mono">88%</div><div className="lbl">of India's crude oil is imported</div></div>
        <div className="home__stat"><div className="val mono">40–45%</div><div className="lbl">transits the Strait of Hormuz</div></div>
        <div className="home__stat"><div className="val mono">9.5 days</div><div className="lbl">of consumption held in reserve</div></div>
      </section>

      <section className="home__features" id="features">
        {FEATURES.map((f) => (
          <div className="home__feature" key={f.title}>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
