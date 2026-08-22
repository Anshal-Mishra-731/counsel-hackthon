import { tierForSeverity, TIER_COLOR_VAR, formatBpd } from "../lib/format";

// Origin -> strait (chokepoint) -> India. When severity is high, the strait visibly cracks.
export default function SupplyFlowDiagram({ severity, dailyBpd }) {
  const tier = tierForSeverity(severity);
  const color = `var(${TIER_COLOR_VAR[tier]})`;
  const broken = severity >= 0.6;

  return (
    <div className="flow">
      <svg width="100%" height="64" viewBox="0 0 320 64" preserveAspectRatio="none">
        <circle cx="16" cy="32" r="5" fill="var(--text-secondary)" />
        <text x="16" y="52" textAnchor="middle" className="flow__label">SUPPLIER</text>
        <line
          x1="21" y1="32" x2="140" y2="32"
          stroke={broken ? "var(--tier-critical)" : color}
          strokeWidth="2"
          strokeDasharray={broken ? "0" : "6 5"}
          className={broken ? "" : "flow__dash"}
        />
        <path d="M 148 14 C 156 14, 156 32, 164 32" stroke="var(--text-secondary)" strokeWidth="1.4" fill="none" />
        <path d="M 148 50 C 156 50, 156 32, 164 32" stroke="var(--text-secondary)" strokeWidth="1.4" fill="none" />
        {broken ? (
          <g>
            <line x1="152" y1="22" x2="160" y2="42" stroke="var(--tier-critical)" strokeWidth="2.4" strokeLinecap="round" />
            <line x1="160" y1="22" x2="152" y2="42" stroke="var(--tier-critical)" strokeWidth="2.4" strokeLinecap="round" />
          </g>
        ) : null}
        <line
          x1="164" y1="32" x2="284" y2="32"
          stroke={broken ? "var(--tier-critical)" : color}
          strokeWidth="2"
          strokeDasharray={broken ? "0" : "6 5"}
          className={broken ? "" : "flow__dash"}
        />
        <circle cx="290" cy="32" r="6" fill="var(--accent-cyan)" />
        <text x="290" y="52" textAnchor="middle" className="flow__label">INDIA</text>
      </svg>
      <div className="flow__caption mono">
        <span style={{ color }}>{broken ? "BLOCKED" : "FLOWING"}</span>
        <span className="flow__caption-sep">·</span>
        <span>{formatBpd(dailyBpd)} at risk</span>
      </div>
      <style>{`
        .flow { width: 100%; }
        .flow__label { font-family: var(--font-mono); font-size: 8px; fill: var(--text-muted); letter-spacing: 0.06em; }
        .flow__dash { animation: flow-move 1.4s linear infinite; }
        @keyframes flow-move { to { stroke-dashoffset: -22; } }
        .flow__caption { display: flex; gap: 8px; justify-content: center; font-size: 11px; color: var(--text-secondary); margin-top: 2px; }
        .flow__caption-sep { color: var(--text-muted); }
      `}</style>
    </div>
  );
}
