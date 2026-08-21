import { useMemo, useState } from "react";
import {
  MAP_VIEWBOX,
  MAP_WIDTH,
  MAP_HEIGHT,
  LAND_PATH,
  MAP_POINTS,
  OFF_MAP_SUPPLIERS,
} from "../lib/worldMapData";
import { tierForSeverity, TIER_COLOR_VAR, TIER_LABEL, slugifyCountry, formatBpd } from "../lib/format";

// Which map points a given corridor's flow passes through, origin-side first.
const CORRIDOR_ROUTE = {
  strait_of_hormuz: ["strait_of_hormuz", "india_hub"],
  red_sea: ["suez", "bab_el_mandeb", "india_hub"],
  cape_of_good_hope: ["cape_of_good_hope", "india_hub"],
};

// Which chokepoint a supplier's traffic is considered to route through, for
// drawing the thin origin -> chokepoint feeder line.
const SUPPLIER_GATEWAY = {
  iraq: "strait_of_hormuz",
  saudi_arabia: "strait_of_hormuz",
  united_arab_emirates: "strait_of_hormuz",
  kuwait: "strait_of_hormuz",
  iran: "strait_of_hormuz",
  oman: "strait_of_hormuz",
  russia: "suez",
  azerbaijan: "suez",
  kazakhstan: "suez",
  nigeria: "cape_of_good_hope",
  angola: "cape_of_good_hope",
};

export default function WorldMap({ corridors }) {
  const entries = useMemo(
    () => Object.entries(corridors).filter(([, v]) => !v.note),
    [corridors]
  );
  const [activeKey, setActiveKey] = useState(
    () => entries.slice().sort((a, b) => b[1].scenario.severity - a[1].scenario.severity)[0]?.[0]
  );

  const india = MAP_POINTS.india_hub;

  return (
    <div className="worldmap">
      <div className="worldmap__legend">
        {entries.map(([key, data]) => {
          const tier = tierForSeverity(data.scenario.severity);
          const color = `var(${TIER_COLOR_VAR[tier]})`;
          const active = key === activeKey;
          return (
            <button
              key={key}
              className={`worldmap__legend-item${active ? " worldmap__legend-item--active" : ""}`}
              style={{ "--row-accent": color }}
              onClick={() => setActiveKey(key)}
              aria-pressed={active}
            >
              <span className="worldmap__legend-dot" />
              <span className="worldmap__legend-name">{data.scenario.corridor}</span>
              <span className="worldmap__legend-sev mono">{Math.round(data.scenario.severity * 100)}%</span>
            </button>
          );
        })}
      </div>

      <div className="worldmap__canvas">
        <svg viewBox={MAP_VIEWBOX} width="100%" height="100%" role="img" aria-label="Map of India's crude oil import corridors">
          <defs>
            <radialGradient id="wm-vignette" cx="50%" cy="38%" r="75%">
              <stop offset="0%" stopColor="rgba(55,201,224,0.05)" />
              <stop offset="100%" stopColor="rgba(5,7,13,0)" />
            </radialGradient>
            <radialGradient id="wm-ping" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity="0.5" />
              <stop offset="100%" stopColor="var(--accent-cyan)" stopOpacity="0" />
            </radialGradient>
          </defs>

          <rect x="0" y="0" width={MAP_WIDTH} height={MAP_HEIGHT} fill="url(#wm-vignette)" />

          {/* radar sweep, centered on India — the "live risk radar" signature */}
          <g style={{ transformOrigin: `${india[0]}px ${india[1]}px` }} className="worldmap__sweep">
            <path
              d={`M ${india[0]} ${india[1]} L ${india[0] + 260} ${india[1]} A 260 260 0 0 0 ${india[0] + 184} ${india[1] - 184} Z`}
              fill="var(--accent-cyan)"
              opacity="0.05"
            />
          </g>

          <path d={LAND_PATH} className="worldmap__land" />

          {/* corridor routes */}
          {entries.map(([key, data]) => {
            const tier = tierForSeverity(data.scenario.severity);
            const color = `var(${TIER_COLOR_VAR[tier]})`;
            const broken = data.scenario.severity >= 0.6;
            const route = CORRIDOR_ROUTE[key] || [];
            const pts = route.map((p) => MAP_POINTS[p]).filter(Boolean);
            if (pts.length < 2) return null;
            const d = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0]} ${p[1]}`).join(" ");
            const isActive = key === activeKey;
            return (
              <path
                key={key}
                d={d}
                fill="none"
                stroke={broken ? "var(--tier-critical)" : color}
                strokeWidth={isActive ? 2.6 : 1.4}
                strokeLinecap="round"
                strokeDasharray={broken ? "1 7" : "5 5"}
                opacity={isActive ? 0.95 : 0.35}
                className="worldmap__route"
              />
            );
          })}

          {/* supplier feeder dots — only for the active corridor, to keep the map legible */}
          {activeKey &&
            corridors[activeKey] &&
            corridors[activeKey].affected_suppliers?.map((s) => {
              const slug = slugifyCountry(s.country);
              const p = MAP_POINTS[slug];
              const gateway = MAP_POINTS[SUPPLIER_GATEWAY[slug]];
              if (!p) return null;
              const r = 3 + 5 * Math.min(1, s.lost_bpd / 1_600_000);
              return (
                <g key={s.country}>
                  {gateway && (
                    <line
                      x1={p[0]} y1={p[1]} x2={gateway[0]} y2={gateway[1]}
                      stroke="var(--text-muted)" strokeWidth="0.8" strokeDasharray="2 3" opacity="0.5"
                    />
                  )}
                  <circle cx={p[0]} cy={p[1]} r={r} fill="var(--tier-critical)" opacity="0.85">
                    <title>{`${s.country}: -${formatBpd(s.lost_bpd)}`}</title>
                  </circle>
                </g>
              );
            })}

          {/* chokepoint markers */}
          {entries.map(([key, data]) => {
            const routeKey = CORRIDOR_ROUTE[key]?.[0];
            const p = MAP_POINTS[routeKey];
            if (!p) return null;
            const tier = tierForSeverity(data.scenario.severity);
            const color = `var(${TIER_COLOR_VAR[tier]})`;
            const isActive = key === activeKey;
            return (
              <g
                key={key}
                transform={`translate(${p[0]}, ${p[1]})`}
                className="worldmap__marker"
                onClick={() => setActiveKey(key)}
                tabIndex={0}
                role="button"
                aria-label={`${data.scenario.corridor}, severity ${Math.round(data.scenario.severity * 100)}%`}
                onKeyDown={(e) => e.key === "Enter" && setActiveKey(key)}
              >
                {isActive && <circle r="16" fill="url(#wm-ping)" className="worldmap__ping" />}
                <circle r={isActive ? 6.5 : 5} fill={color} stroke="var(--ink-900)" strokeWidth="1.5" />
                <text y="-12" textAnchor="middle" className="worldmap__marker-label mono">
                  {Math.round(data.scenario.severity * 100)}%
                </text>
              </g>
            );
          })}

          {/* India */}
          <g transform={`translate(${india[0]}, ${india[1]})`}>
            <circle r="15" fill="url(#wm-ping)" className="worldmap__ping" />
            <circle r="6" fill="var(--accent-amber)" stroke="var(--ink-900)" strokeWidth="1.5" />
            <text y="20" textAnchor="middle" className="worldmap__india-label mono">INDIA</text>
          </g>
        </svg>
      </div>

      {activeKey && corridors[activeKey] && (
        <div className="worldmap__detail">
          <div>
            <span className="worldmap__detail-label">Selected corridor</span>
            <h4>{corridors[activeKey].scenario.corridor}</h4>
          </div>
          <p>{TIER_LABEL[tierForSeverity(corridors[activeKey].scenario.severity)]} · {formatBpd(corridors[activeKey].baseline.daily_shortfall_bpd)} at risk</p>
          <a href={`#corridor-${activeKey}`} className="worldmap__detail-link">Jump to full corridor report ↓</a>
        </div>
      )}

      {OFF_MAP_SUPPLIERS.length > 0 && (
        <p className="worldmap__offmap">
          Also sourcing from {OFF_MAP_SUPPLIERS.join(", ")} — outside this regional frame.
        </p>
      )}

      <style>{`
        .worldmap {
          display: grid;
          grid-template-columns: 200px 1fr;
          grid-template-rows: auto auto;
          gap: 16px 20px;
        }
        .worldmap__legend {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .worldmap__legend-item {
          all: unset;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 9px 10px;
          border-radius: var(--radius-sm);
          border: 1px solid transparent;
          font-size: 12px;
          color: var(--text-secondary);
        }
        .worldmap__legend-item:hover {
          background: var(--ink-800);
        }
        .worldmap__legend-item--active {
          border-color: var(--hairline-strong);
          background: var(--ink-800);
          color: var(--text-primary);
        }
        .worldmap__legend-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: var(--row-accent);
          flex-shrink: 0;
        }
        .worldmap__legend-name {
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .worldmap__legend-sev {
          color: var(--text-muted);
          font-size: 10.5px;
        }
        .worldmap__canvas {
          grid-row: 1 / 3;
          grid-column: 2;
          aspect-ratio: ${MAP_WIDTH} / ${MAP_HEIGHT};
          background: radial-gradient(circle at 50% 30%, var(--ink-800), var(--ink-900));
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          overflow: hidden;
        }
        .worldmap__land {
          fill: var(--ink-700);
          stroke: var(--hairline-strong);
          stroke-width: 0.6;
        }
        .worldmap__route {
          transition: opacity 0.25s ease, stroke-width 0.25s ease;
        }
        .worldmap__marker {
          cursor: pointer;
        }
        .worldmap__marker-label {
          font-size: 8.5px;
          fill: var(--text-secondary);
        }
        .worldmap__india-label {
          font-size: 8.5px;
          fill: var(--text-secondary);
          letter-spacing: 0.06em;
        }
        .worldmap__ping {
          animation: wm-ping 2.4s ease-out infinite;
          transform-origin: center;
        }
        .worldmap__sweep {
          animation: wm-sweep 6s linear infinite;
        }
        @keyframes wm-ping {
          0% { transform: scale(0.4); opacity: 0.9; }
          100% { transform: scale(1.6); opacity: 0; }
        }
        @keyframes wm-sweep {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .worldmap__detail {
          grid-column: 1;
          grid-row: 2;
          padding: 12px 14px;
          background: var(--ink-800);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-md);
          display: flex;
          flex-direction: column;
          gap: 6px;
          align-self: start;
        }
        .worldmap__detail-label {
          font-size: 9px;
          letter-spacing: 0.06em;
          color: var(--text-muted);
        }
        .worldmap__detail h4 {
          font-size: 13px;
          margin-top: 2px;
        }
        .worldmap__detail p {
          font-size: 11.5px;
          color: var(--text-secondary);
          margin: 0;
        }
        .worldmap__detail-link {
          font-size: 11.5px;
          color: var(--accent-cyan);
          margin-top: 2px;
        }
        .worldmap__offmap {
          grid-column: 1 / -1;
          margin: 0;
          font-size: 11px;
          color: var(--text-muted);
        }
        @media (max-width: 760px) {
          .worldmap {
            grid-template-columns: 1fr;
          }
          .worldmap__canvas {
            grid-row: 2;
            grid-column: 1;
          }
          .worldmap__detail {
            grid-row: 3;
            grid-column: 1;
          }
        }
      `}</style>
    </div>
  );
}
