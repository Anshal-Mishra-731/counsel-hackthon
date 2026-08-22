import { Link } from "react-router-dom";
import { formatNumber } from "../lib/format";

export default function Header({ baselineYear, totalBpd, source, lastUpdated }) {
  return (
    <header className="header">
      <Link to="/" className="header__brand">
        <ChokepointMark />
        <div>
          <h1>Chokepoint</h1>
          <p className="header__subtitle">India crude supply risk monitor</p>
        </div>
      </Link>

      <div className="header__baseline mono">
        <span className="header__baseline-label">BASELINE</span>
        <span>{formatNumber(totalBpd)} bpd</span>
        <span className="header__dot">·</span>
        <span>FY {baselineYear}</span>
      </div>

      <div className="header__status">
        <span className={`status-dot status-dot--${source}`} aria-hidden="true" />
        <span className="mono">
          {source === "live" ? "LIVE" : "SAMPLE DATA"}
          {lastUpdated && ` · updated ${lastUpdated.toLocaleTimeString("en-IN", { hour12: false })}`}
        </span>
      </div>

      <style>{`
        .header {
          display: flex;
          align-items: center;
          gap: 28px;
          padding: 18px 32px;
          border-bottom: 1px solid var(--hairline);
          background: linear-gradient(180deg, rgba(10,15,28,0.92), rgba(10,15,28,0.5));
          backdrop-filter: blur(10px);
          position: sticky;
          top: 0;
          z-index: 20;
          flex-wrap: wrap;
        }
        .header__brand {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .header__brand h1 {
          font-family: var(--font-display);
          font-size: 19px;
          font-weight: 700;
          margin: 0;
          letter-spacing: 0.01em;
        }
        .header__subtitle {
          margin: 0;
          font-size: 11.5px;
          color: var(--text-muted);
        }
        .header__baseline {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12.5px;
          color: var(--text-secondary);
          padding: 6px 14px;
          border: 1px solid var(--hairline);
          border-radius: 999px;
          background: var(--ink-800);
        }
        .header__baseline-label {
          color: var(--text-muted);
          letter-spacing: 0.08em;
          font-size: 9.5px;
        }
        .header__dot { color: var(--text-muted); }
        .header__status {
          margin-left: auto;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 11.5px;
          color: var(--text-secondary);
        }
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          display: inline-block;
        }
        .status-dot--live {
          background: var(--tier-safe);
          animation: pulse 2s infinite;
        }
        .status-dot--sample {
          background: var(--text-muted);
        }
        @keyframes pulse {
          0% { box-shadow: 0 0 0 0 rgba(45, 217, 181, 0.5); }
          70% { box-shadow: 0 0 0 8px rgba(45, 217, 181, 0); }
          100% { box-shadow: 0 0 0 0 rgba(45, 217, 181, 0); }
        }
      `}</style>
    </header>
  );
}

export function ChokepointMark({ size = 30 }) {
  // A narrowing strait glyph - the literal "chokepoint" mark, used as the brand icon.
  return (
    <svg width={size} height={size} viewBox="0 0 30 30" fill="none" aria-hidden="true">
      <path d="M2 6 C 10 6, 12 15, 15 15 C 18 15, 20 6, 28 6" stroke="var(--accent-cyan)" strokeWidth="1.6" fill="none" />
      <path d="M2 24 C 10 24, 12 15, 15 15 C 18 15, 20 24, 28 24" stroke="var(--accent-cyan)" strokeWidth="1.6" fill="none" />
      <circle cx="15" cy="15" r="2" fill="var(--accent-amber)" />
    </svg>
  );
}
