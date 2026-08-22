import { useMemo, useState } from "react";
import { simulateCorridor } from "../lib/simulate";
import { formatBpd, tierForSeverity, TIER_COLOR_VAR, TIER_LABEL } from "../lib/format";

export default function SimulationPanel({ corridors }) {
  const entries = useMemo(
    () => Object.entries(corridors).filter(([, v]) => !v.note),
    [corridors]
  );
  const [key, setKey] = useState(entries[0]?.[0]);
  const corridor = corridors[key];
  const baseSeverity = corridor.scenario.severity;
  const [severityPct, setSeverityPct] = useState(Math.round(baseSeverity * 100));

  const sim = simulateCorridor(corridor, severityPct / 100);
  const tier = tierForSeverity(severityPct / 100);
  const color = `var(${TIER_COLOR_VAR[tier]})`;
  const deltaShortfall = sim.dailyShortfallBpd - corridor.baseline.daily_shortfall_bpd;

  function selectCorridor(k) {
    setKey(k);
    setSeverityPct(Math.round(corridors[k].scenario.severity * 100));
  }

  return (
    <div className="sim">
      <div className="sim__tabs">
        {entries.map(([k, d]) => (
          <button
            key={k}
            className={`sim__tab${k === key ? " sim__tab--active" : ""}`}
            onClick={() => selectCorridor(k)}
          >
            {d.scenario.corridor}
          </button>
        ))}
      </div>

      <div className="sim__body">
        <div className="sim__control">
          <div className="sim__control-head">
            <span>Escalation severity</span>
            <span className="mono sim__control-value" style={{ color }}>{severityPct}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={severityPct}
            onChange={(e) => setSeverityPct(Number(e.target.value))}
            className="sim__slider"
            style={{ "--slider-color": color }}
            aria-label={`${corridor.scenario.corridor} severity`}
          />
          <div className="sim__control-scale mono">
            <span>Tension</span>
            <span>Posturing</span>
            <span>Escalation</span>
            <span>Breakdown</span>
          </div>
          <p className="sim__tier-label" style={{ color }}>{TIER_LABEL[tier]}</p>
        </div>

        <div className="sim__readouts">
          <Readout
            label="Daily shortfall"
            value={formatBpd(sim.dailyShortfallBpd)}
            delta={deltaShortfall !== 0 ? `${deltaShortfall > 0 ? "+" : ""}${formatBpd(deltaShortfall)} vs last run` : "matches last backend run"}
          />
          <Readout label="Supply drop" value={`${sim.supplyDropPct.toFixed(1)}%`} />
          <Readout label="Est. price spike" value={`+${sim.priceSpikePct.toFixed(1)}%`} accent />
          <Readout label="Est. gross loss" value={`${(sim.grossLossBbl / 1_000_000).toFixed(1)}M bbl`} />
        </div>
      </div>

      <p className="sim__note">
        Instant client-side re-projection using the backend's own severity → shortfall → price-spike
        ratios, holding replacement lead-time fixed. For a fully re-solved routing plan at this
        severity, trigger a fresh backend run.
      </p>

      <style>{`
        .sim {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .sim__tabs {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
        .sim__tab {
          all: unset;
          cursor: pointer;
          font-size: 12px;
          padding: 7px 14px;
          border-radius: 999px;
          border: 1px solid var(--hairline);
          color: var(--text-secondary);
        }
        .sim__tab:hover { background: var(--ink-800); }
        .sim__tab--active {
          background: var(--accent-cyan-dim);
          border-color: var(--accent-cyan);
          color: var(--text-primary);
        }
        .sim__body {
          display: grid;
          grid-template-columns: 1.1fr 1fr;
          gap: 24px;
        }
        .sim__control {
          background: var(--ink-800);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-md);
          padding: 16px 18px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .sim__control-head {
          display: flex;
          justify-content: space-between;
          font-size: 12.5px;
          color: var(--text-secondary);
        }
        .sim__control-value {
          font-size: 15px;
          font-weight: 700;
        }
        .sim__slider {
          -webkit-appearance: none;
          appearance: none;
          width: 100%;
          height: 4px;
          border-radius: 4px;
          background: linear-gradient(90deg, var(--tier-safe), var(--tier-moderate), var(--tier-high), var(--tier-critical));
          margin: 10px 0 4px;
        }
        .sim__slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: var(--slider-color, var(--accent-cyan));
          border: 2px solid var(--ink-900);
          box-shadow: 0 0 0 3px rgba(255,255,255,0.08);
          cursor: pointer;
        }
        .sim__slider::-moz-range-thumb {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: var(--slider-color, var(--accent-cyan));
          border: 2px solid var(--ink-900);
          cursor: pointer;
        }
        .sim__control-scale {
          display: flex;
          justify-content: space-between;
          font-size: 8.5px;
          letter-spacing: 0.03em;
          color: var(--text-muted);
        }
        .sim__tier-label {
          font-size: 12.5px;
          font-weight: 600;
          margin-top: 4px;
        }
        .sim__readouts {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }
        .sim__note {
          font-size: 11px;
          color: var(--text-muted);
          line-height: 1.6;
          max-width: 640px;
        }
        @media (max-width: 720px) {
          .sim__body { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}

function Readout({ label, value, delta, accent }) {
  return (
    <div className="readout">
      <span className="readout__label">{label}</span>
      <span className={`readout__value mono${accent ? " readout__value--accent" : ""}`}>{value}</span>
      {delta && <span className="readout__delta mono">{delta}</span>}
      <style>{`
        .readout {
          background: var(--ink-800);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-sm);
          padding: 10px 12px;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .readout__label {
          font-size: 9.5px;
          color: var(--text-muted);
          letter-spacing: 0.03em;
        }
        .readout__value {
          font-size: 17px;
          font-weight: 700;
          color: var(--text-primary);
        }
        .readout__value--accent {
          color: var(--accent-amber);
        }
        .readout__delta {
          font-size: 9.5px;
          color: var(--text-muted);
        }
      `}</style>
    </div>
  );
}
