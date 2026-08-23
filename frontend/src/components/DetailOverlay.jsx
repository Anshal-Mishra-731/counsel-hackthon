import React, { useEffect, useState } from "react";
import { api, RISK_COLORS, RISK_LABELS } from "../lib/api";
import RiskGauge from "./RiskGauge.jsx";
import SupplyFlowDiagram from "./SupplyFlowDiagram.jsx";
import SupplierTable from "./SupplierTable.jsx";
import AlternativeSourceTable from "./AlternativeSourceTable.jsx";
import EconomicPanel from "./EconomicPanel.jsx";

function fmt(n) {
  if (n === undefined || n === null) return "—";
  return n.toLocaleString();
}

export default function DetailOverlay({ corridorKey, onClose }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .corridorDetail(corridorKey)
      .then((d) => !cancelled && setDetail(d))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [corridorKey]);

  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="overlay-backdrop" onClick={onClose}>
      <div className="overlay-panel" onClick={(e) => e.stopPropagation()}>
        {loading && <div className="note-box">Loading corridor intelligence…</div>}
        {error && <div className="note-box">Couldn't reach the backend: {error}</div>}

        {detail && (
          <>
            <div className="overlay-header">
              <div>
                <div className="overlay-eyebrow">Corridor Detail</div>
                <div className="overlay-title">{detail.name}</div>
                <span className="mode-tag">{detail.mode}</span>
              </div>
              <button className="close-btn" onClick={onClose}>✕</button>
            </div>

            <div
              className="risk-banner"
              style={{
                background: `${RISK_COLORS[detail.risk_bucket]}1a`,
                borderColor: RISK_COLORS[detail.risk_bucket],
                display: "flex",
                alignItems: "center",
                gap: 16,
              }}
            >
              <RiskGauge severity={(detail.risk_score || 0) / 100} size={92} />
              <div style={{ flex: 1 }}>
                <div
                  className="risk-banner-label"
                  style={{ color: RISK_COLORS[detail.risk_bucket] }}
                >
                  {RISK_LABELS[detail.risk_bucket]} risk
                  {detail.traffic_halted ? " · traffic halted" : ""}
                </div>
                <div className="risk-banner-summary">{detail.summary}</div>
              </div>
            </div>

            {detail.baseline && (
              <>
                <SupplyFlowDiagram
                  severity={(detail.risk_score || 0) / 100}
                  dailyBpd={
                    detail.baseline.daily_shortfall_bpd ??
                    detail.baseline.corridor_dependent_bpd ??
                    0
                  }
                />

                <div className="stat-grid">
                  <div className="stat-card">
                    <div className="val">{fmt(detail.baseline.india_total_import_bpd)}</div>
                    <div className="lbl">India total import (bpd)</div>
                  </div>
                  <div className="stat-card">
                    <div className="val">{fmt(detail.baseline.corridor_dependent_bpd)}</div>
                    <div className="lbl">Corridor-dependent bpd</div>
                  </div>
                  <div className="stat-card">
                    <div className="val">{fmt(detail.supply_impact?.net_gap_bbl)}</div>
                    <div className="lbl">Net barrel gap</div>
                  </div>
                  <div className="stat-card">
                    <div className="val">
                      {detail.economic_estimates?.estimated_crude_price_spike_pct}%
                    </div>
                    <div className="lbl">Est. price spike</div>
                  </div>
                </div>
              </>
            )}

            <div className="section-title">Affected countries / suppliers</div>
            <SupplierTable suppliers={detail.affected_suppliers} />

            <div className="section-title">Alternate routes / suppliers</div>
            <AlternativeSourceTable sources={detail.alternative_sources} />

            {detail.economic_estimates && detail.supply_impact && (
              <>
                <div className="section-title">Economic impact</div>
                <EconomicPanel
                  economics={detail.economic_estimates}
                  supplyImpact={detail.supply_impact}
                />
              </>
            )}

            {detail.derived_lead_time && (
              <>
                <div className="section-title">Replacement timeline</div>
                <div className="stat-grid">
                  <div className="stat-card">
                    <div className="val">
                      {detail.derived_lead_time.estimated_replacement_days}d
                    </div>
                    <div className="lbl">Est. replacement time</div>
                  </div>
                  <div className="stat-card">
                    <div className="val">
                      {fmt(detail.derived_lead_time.residual_daily_shortfall_bpd)}
                    </div>
                    <div className="lbl">Residual daily shortfall</div>
                  </div>
                </div>
              </>
            )}

            {/* NEW PHASE 4: Strategic Petroleum Reserve Plan */}
            {detail.phase4_spr_summary && Object.keys(detail.phase4_spr_summary).length > 0 && (
              <>
                <div className="section-title">Phase 4: Reserve Drawdown Plan</div>
                <div className="stat-grid">
                  <div className="stat-card" style={{ borderColor: "var(--accent-cyan)" }}>
                    <div className="val" style={{ color: "var(--accent-cyan)" }}>
                      {detail.phase4_spr_summary.crisis_duration_days || "—"}d
                    </div>
                    <div className="lbl">Strategic cover used</div>
                  </div>
                  <div className="stat-card" style={{ borderColor: "var(--accent-cyan)" }}>
                    <div className="val" style={{ color: "var(--accent-cyan)" }}>
                      {detail.phase4_spr_summary.isprl_summary?.total_drawn_barrels 
                        ? `${(detail.phase4_spr_summary.isprl_summary.total_drawn_barrels / 1_000_000).toFixed(1)}M` 
                        : "—"}
                    </div>
                    <div className="lbl">Total barrels drawn</div>
                  </div>
                </div>
              </>
            )}

            {!detail.baseline && detail.note && (
              <div className="note-box">{detail.note}</div>
            )}
          </>
        )}
      </div>
    </div>
  );
}