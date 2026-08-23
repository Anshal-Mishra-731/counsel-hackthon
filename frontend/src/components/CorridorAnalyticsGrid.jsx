import React, { useEffect, useState } from "react";
import { api, RISK_COLORS, RISK_LABELS } from "../lib/api";
import RiskGauge from "./RiskGauge.jsx";
import SupplierTable from "./SupplierTable.jsx";
import AlternativeSourceTable from "./AlternativeSourceTable.jsx";
import EconomicPanel from "./EconomicPanel.jsx";

export default function CorridorAnalyticsGrid() {
  const [corridors, setCorridors] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api
      .analytics()
      .then((d) => !cancelled && setCorridors(d.corridors))
      .catch((e) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return <div className="note-box">Couldn't load per-corridor analytics: {error}</div>;
  }
  if (!corridors) {
    return <div className="note-box">Loading full corridor breakdown…</div>;
  }

  return (
    <div className="corridor-analytics-grid">
      {corridors.map((c) => (
        <div className="corridor-analytics-card" key={c.key}>
          <div className="corridor-analytics-head">
            <div>
              <h3>{c.name}</h3>
              <span className="mono" style={{ color: RISK_COLORS[c.risk_bucket] }}>
                {RISK_LABELS[c.risk_bucket]} · {c.risk_score}/100
                {c.traffic_halted ? " · traffic halted" : ""}
              </span>
            </div>
            <RiskGauge severity={(c.risk_score || 0) / 100} size={72} />
          </div>
          <p className="corridor-analytics-summary">{c.summary}</p>

          {c.affected_suppliers?.length > 0 || c.alternative_sources?.length > 0 ? (
            <>
              <h4>Affected suppliers</h4>
              <SupplierTable suppliers={c.affected_suppliers} />
              
              <h4>Alternate sources</h4>
              <AlternativeSourceTable sources={c.alternative_sources} />
              
              {c.economic_estimates && c.supply_impact && (
                <>
                  <h4>Economic impact</h4>
                  <EconomicPanel economics={c.economic_estimates} supplyImpact={c.supply_impact} />
                </>
              )}

              {/* NEW PHASE 4: Mini Strategic Reserve Plan */}
              {c.phase4_spr_summary && Object.keys(c.phase4_spr_summary).length > 0 && (
                <>
                  <h4>Phase 4 Reserve Plan</h4>
                  <div style={{ display: "flex", gap: "12px" }}>
                    <div style={{ flex: 1, padding: "10px", background: "var(--bg-panel-2)", border: "1px solid var(--accent-cyan)", borderRadius: "var(--radius-sm)" }}>
                      <div className="mono" style={{ fontSize: "16px", fontWeight: 700, color: "var(--accent-cyan)" }}>
                        {c.phase4_spr_summary.crisis_duration_days || "—"}d
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)", letterSpacing: "0.02em" }}>Cover drawn</div>
                    </div>
                    <div style={{ flex: 1, padding: "10px", background: "var(--bg-panel-2)", border: "1px solid var(--accent-cyan)", borderRadius: "var(--radius-sm)" }}>
                      <div className="mono" style={{ fontSize: "16px", fontWeight: 700, color: "var(--accent-cyan)" }}>
                        {c.phase4_spr_summary.isprl_summary?.total_drawn_barrels 
                          ? `${(c.phase4_spr_summary.isprl_summary.total_drawn_barrels / 1_000_000).toFixed(1)}M` 
                          : "—"}
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)", letterSpacing: "0.02em" }}>Barrels active</div>
                    </div>
                  </div>
                </>
              )}
            </>
          ) : (
            <p className="note-box">
              {c.note || "No barrel-level data available for this corridor."}
            </p>
          )}
        </div>
      ))}
      <style>{`
        .corridor-analytics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
          gap: 16px;
          margin-top: 12px;
        }
        .corridor-analytics-card {
          background: var(--bg-panel, #0f1e2e);
          border: 1px solid var(--hairline, #223447);
          border-radius: 12px;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .corridor-analytics-head {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 10px;
        }
        .corridor-analytics-head h3 {
          margin: 0 0 4px;
          font-size: 15px;
        }
        .corridor-analytics-summary {
          font-size: 12.5px;
          color: var(--text-muted, #8ba3ba);
          margin: 0 0 4px;
        }
        .corridor-analytics-card h4 {
          margin: 10px 0 4px;
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--text-muted, #8ba3ba);
        }
      `}</style>
    </div>
  );
}