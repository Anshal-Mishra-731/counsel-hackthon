import { useState } from "react";
import RiskGauge from "./RiskGauge";
import SupplyFlowDiagram from "./SupplyFlowDiagram";
import SupplierTable from "./SupplierTable";
import AlternativeSourceTable from "./AlternativeSourceTable";
import EconomicPanel from "./EconomicPanel";
import { tierForSeverity, TIER_LABEL, TIER_COLOR_VAR, formatNumber } from "../lib/format";

export default function CorridorCard({ corridorKey, corridorData, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);

  if (corridorData.note) {
    // corridor with no crude-dependency data - render a quiet placeholder, not a fake number
    return (
      <div className="corridor-card corridor-card--empty" id={`corridor-${corridorKey}`}>
        <h3>{corridorData.phase1_context?.name || corridorKey}</h3>
        <p>{corridorData.note}</p>
        <style>{`
          .corridor-card--empty {
            padding: 20px;
            border: 1px dashed var(--hairline);
            border-radius: var(--radius-lg);
            color: var(--text-muted);
            font-size: 12.5px;
          }
          .corridor-card--empty h3 {
            font-family: var(--font-display);
            font-size: 15px;
            color: var(--text-secondary);
            margin: 0 0 6px;
          }
        `}</style>
      </div>
    );
  }

  const { scenario, baseline, affected_suppliers, alternative_sources, derived_lead_time, supply_impact, economic_estimates, phase1_context } =
    corridorData;
  const tier = tierForSeverity(scenario.severity);
  const color = `var(${TIER_COLOR_VAR[tier]})`;

  return (
    <div className="corridor-card" id={`corridor-${corridorKey}`} style={{ "--card-accent": color }}>
      <button className="corridor-card__head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <div className="corridor-card__title">
          <span className="corridor-card__tier-dot" />
          <div>
            <h3>{scenario.corridor}</h3>
            <span className="corridor-card__tier-label">{TIER_LABEL[tier]}</span>
          </div>
        </div>
        <RiskGauge severity={scenario.severity} size={72} />
      </button>

      <div className="corridor-card__body">
        <SupplyFlowDiagram
          severity={scenario.severity}
          dailyBpd={baseline.daily_shortfall_bpd}
          corridorName={scenario.corridor}
        />

        <div className="corridor-card__stat-row mono">
          <div>
            <span className="stat-label">Replacement ETA</span>
            <span className="stat-value">{derived_lead_time.estimated_replacement_days}d</span>
          </div>
          <div>
            <span className="stat-label">Gross loss</span>
            <span className="stat-value">{(supply_impact.gross_loss_bbl / 1_000_000).toFixed(1)}M bbl</span>
          </div>
          <div>
            <span className="stat-label">Risk score</span>
            <span className="stat-value">{phase1_context?.risk_score ?? "—"}/100</span>
          </div>
        </div>

        <button className="corridor-card__expand-toggle" onClick={() => setOpen(!open)}>
          {open ? "Hide details" : "Show suppliers, alternatives & economics"}
          <ChevronIcon open={open} />
        </button>

        {open && (
          <div className="corridor-card__details">
            <Section title="Affected suppliers">
              <SupplierTable suppliers={affected_suppliers} />
            </Section>
            <Section title="Alternative sources (fastest first)">
              <AlternativeSourceTable sources={alternative_sources} />
            </Section>
            <Section title="Economic impact">
              <EconomicPanel economics={economic_estimates} supplyImpact={supply_impact} />
            </Section>
            {derived_lead_time.residual_daily_shortfall_bpd > 0 && (
              <p className="corridor-card__residual-note">
                ⚠ {formatNumber(derived_lead_time.residual_daily_shortfall_bpd)} bpd cannot be covered by
                available alternative capacity — chronic shortfall persists beyond the replacement window.
              </p>
            )}
          </div>
        )}
      </div>

      <style>{`
        .corridor-card {
          background: var(--ink-700);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          overflow: hidden;
          display: flex;
          flex-direction: column;
          box-shadow: var(--shadow-card);
          scroll-margin-top: 96px;
        }
        .corridor-card__head {
          all: unset;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 18px 20px;
          border-bottom: 1px solid var(--hairline);
        }
        .corridor-card__title {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .corridor-card__tier-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--card-accent);
          flex-shrink: 0;
          box-shadow: 0 0 0 4px color-mix(in srgb, var(--card-accent) 18%, transparent);
        }
        .corridor-card__title h3 {
          font-family: var(--font-display);
          font-size: 15px;
          margin: 0;
          color: var(--text-primary);
        }
        .corridor-card__tier-label {
          font-size: 10.5px;
          color: var(--text-muted);
        }
        .corridor-card__body {
          padding: 18px 20px 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .corridor-card__stat-row {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
        }
        .corridor-card__stat-row > div {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .stat-label {
          font-size: 9.5px;
          color: var(--text-muted);
          letter-spacing: 0.04em;
        }
        .stat-value {
          font-size: 15px;
          font-weight: 600;
          color: var(--text-primary);
        }
        .corridor-card__expand-toggle {
          all: unset;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          font-size: 11.5px;
          color: var(--accent-cyan);
          padding: 8px;
          border: 1px solid var(--hairline);
          border-radius: var(--radius-sm);
          transition: background 0.15s ease;
        }
        .corridor-card__expand-toggle:hover {
          background: var(--ink-800);
        }
        .corridor-card__details {
          display: flex;
          flex-direction: column;
          gap: 18px;
          padding-top: 4px;
          animation: expand-in 0.2s ease;
        }
        @keyframes expand-in {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .corridor-card__residual-note {
          margin: 0;
          font-size: 11.5px;
          color: var(--tier-high);
          background: var(--tier-high-dim);
          padding: 10px 12px;
          border-radius: var(--radius-sm);
        }
      `}</style>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section>
      <h4 className="section-title">{title}</h4>
      {children}
      <style>{`
        .section-title {
          font-family: var(--font-display);
          font-size: 11.5px;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          color: var(--text-muted);
          margin: 0 0 10px;
        }
      `}</style>
    </section>
  );
}

function ChevronIcon({ open }) {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      style={{ transform: open ? "rotate(180deg)" : "none", transition: "transform 0.2s ease" }}
    >
      <path d="M2 4 L6 8 L10 4" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
