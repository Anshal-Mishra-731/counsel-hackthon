import React, { useEffect, useState } from "react";
import { api, RISK_COLORS, RISK_LABELS } from "../lib/api";
import RiskGauge from "./RiskGauge.jsx";
import SupplierTable from "./SupplierTable.jsx";
import AlternativeSourceTable from "./AlternativeSourceTable.jsx";
import EconomicPanel from "./EconomicPanel.jsx";

export default function CorridorAnalyticsGrid() {
  const [corridors, setCorridors] = useState(null);
  const [error, setError] = useState(null);
  const [expandedPlanKey, setExpandedPlanKey] = useState(null);

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
    return <div className="cag-alert">Unable to load corridor analytics: {error}</div>;
  }
  if (!corridors) {
    return <div className="cag-alert">Loading operational intelligence…</div>;
  }

  const togglePlan = (key) => {
    setExpandedPlanKey((prev) => (prev === key ? null : key));
  };

  return (
    <div className="cag-container">
      {corridors.map((c) => {
        const isPlanOpen = expandedPlanKey === c.key;
        const spr = c.phase4_spr_summary;
        const hasDisruptionData =
          c.affected_suppliers?.length > 0 || c.alternative_sources?.length > 0;

        return (
          <div
            className={`cag-card ${c.traffic_halted ? "cag-card-halted" : ""}`}
            key={c.key}
          >
            {/* Header */}
            <div className="cag-head">
              <div className="cag-title-wrap">
                <div className="cag-title-row">
                  <h3 className="cag-name">{c.name}</h3>
                  <span
                    className="cag-risk-pill"
                    style={{
                      color: RISK_COLORS[c.risk_bucket] || "#2dd4bf",
                      borderColor: `${RISK_COLORS[c.risk_bucket] || "#2dd4bf"}55`,
                      backgroundColor: `${RISK_COLORS[c.risk_bucket] || "#2dd4bf"}15`,
                    }}
                  >
                    {RISK_LABELS[c.risk_bucket] || "Normal"} · {c.risk_score}/100
                  </span>
                  {c.traffic_halted && (
                    <span className="cag-halted-tag">TRAFFIC HALTED</span>
                  )}
                </div>
                <p className="cag-summary">{c.summary}</p>
              </div>
              <div className="cag-gauge-wrap">
                <RiskGauge severity={(c.risk_score || 0) / 100} size={70} />
              </div>
            </div>

            {/* Main Content */}
            {hasDisruptionData ? (
              <div className="cag-body">
                <div className="cag-section">
                  <span className="cag-section-label">Affected Suppliers</span>
                  <SupplierTable suppliers={c.affected_suppliers} />
                </div>

                <div className="cag-section">
                  <span className="cag-section-label">Alternate Rerouting</span>
                  <AlternativeSourceTable sources={c.alternative_sources} />
                </div>

                {c.economic_estimates && c.supply_impact && (
                  <div className="cag-section">
                    <span className="cag-section-label">Economic & Volume Impact</span>
                    <EconomicPanel
                      economics={c.economic_estimates}
                      supplyImpact={c.supply_impact}
                    />
                  </div>
                )}

                {/* Phase 4 SPR Drawer */}
                {spr && Object.keys(spr).length > 0 && (
                  <div className="cag-spr-panel">
                    <div className="cag-spr-top">
                      <div>
                        <span className="cag-spr-title">Phase 4 Strategic Reserve Plan</span>
                        <div className="cag-spr-subtitle">
                          {spr.status || "Reserve Drawdown Optimization Successful"}
                        </div>
                      </div>
                      <button
                        type="button"
                        className={`cag-btn-plan ${isPlanOpen ? "cag-btn-plan-active" : ""}`}
                        onClick={() => togglePlan(c.key)}
                      >
                        {isPlanOpen ? "Hide Plan ▲" : "View 32-Day Plan ↗"}
                      </button>
                    </div>

                    <div className="cag-spr-stats">
                      <div className="cag-spr-stat-box">
                        <span className="cag-spr-val">
                          {spr.crisis_duration_days || "—"}d
                        </span>
                        <span className="cag-spr-lbl">Cover Duration</span>
                      </div>
                      <div className="cag-spr-stat-box">
                        <span className="cag-spr-val">
                          {spr.isprl_summary?.total_drawn_barrels
                            ? `${(spr.isprl_summary.total_drawn_barrels / 1_000_000).toFixed(1)}M`
                            : "—"}
                        </span>
                        <span className="cag-spr-lbl">ISPRL Active Barrels</span>
                      </div>
                      <div className="cag-spr-stat-box">
                        <span className="cag-spr-val">
                          {spr.omc_commercial_summary?.total_drawn_barrels
                            ? `${(spr.omc_commercial_summary.total_drawn_barrels / 1_000_000).toFixed(1)}M`
                            : "—"}
                        </span>
                        <span className="cag-spr-lbl">OMC Commercial Stock</span>
                      </div>
                    </div>

                    {/* Inline Expandable 32-Day Table */}
                    {isPlanOpen && (
                      <div className="cag-drawer">
                        <div className="cag-drawer-header">
                          <span className="cag-drawer-title">
                            Daily Schedule ({spr.crisis_duration_days} Days)
                          </span>
                          <span className="cag-drawer-meta">
                            Unmet Shortfall:{" "}
                            <strong style={{ color: "#34d399" }}>
                              {spr.total_unmet_shortfall_barrels === 0
                                ? "0 bbl (100% Protected)"
                                : `${spr.total_unmet_shortfall_barrels} bbl`}
                            </strong>
                          </span>
                        </div>

                        <div className="cag-table-scroll">
                          <table className="cag-table">
                            <thead>
                              <tr>
                                <th>Timeline</th>
                                <th>Target Deficit</th>
                                <th>Visakhapatnam</th>
                                <th>Mangaluru</th>
                                <th>Padur</th>
                                <th>OMC Buffer</th>
                                <th>Unmet</th>
                              </tr>
                            </thead>
                            <tbody>
                              {spr.daily_drawdown_schedule?.map((row) => (
                                <tr key={row.day}>
                                  <td className="cag-mono cag-strong">Day {row.day}</td>
                                  <td className="cag-mono">
                                    {row.target_deficit_bpd?.toLocaleString()}
                                  </td>
                                  <td className="cag-mono">
                                    {row.cavern_drawdowns_bpd?.[
                                      "Visakhapatnam, Andhra Pradesh"
                                    ]?.toLocaleString() || "0"}
                                  </td>
                                  <td className="cag-mono">
                                    {row.cavern_drawdowns_bpd?.[
                                      "Mangaluru, Karnataka"
                                    ]?.toLocaleString() || "0"}
                                  </td>
                                  <td className="cag-mono">
                                    {row.cavern_drawdowns_bpd?.[
                                      "Padur, Karnataka"
                                    ]?.toLocaleString() || "0"}
                                  </td>
                                  <td className="cag-mono">
                                    {row.omc_drawdown_bpd?.toLocaleString() || "0"}
                                  </td>
                                  <td
                                    className={`cag-mono ${
                                      row.unmet_shortfall_bpd > 0
                                        ? "cag-text-red"
                                        : "cag-text-green"
                                    }`}
                                  >
                                    {row.unmet_shortfall_bpd?.toLocaleString() || "0"}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="cag-normal-note">
                {c.note || "Commercial maritime lanes safe and open. Operating at 100% normal capacity."}
              </div>
            )}
          </div>
        );
      })}

      <style>{`
        .cag-container {
          display: flex;
          flex-direction: column;
          gap: 20px;
          margin-top: 18px;
          width: 100%;
        }
        .cag-card {
          background: #0b1522;
          border: 1px solid #1a2a3c;
          border-radius: 12px;
          padding: 20px 22px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
          transition: border-color 0.2s ease;
        }
        .cag-card:hover {
          border-color: #243b53;
        }
        .cag-card-halted {
          border-color: rgba(244, 63, 94, 0.45);
          box-shadow: 0 4px 24px rgba(244, 63, 94, 0.08);
        }
        .cag-head {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 16px;
        }
        .cag-title-wrap {
          flex: 1;
        }
        .cag-title-row {
          display: flex;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
          margin-bottom: 6px;
        }
        .cag-name {
          font-size: 18px;
          font-weight: 700;
          color: #f8fafc;
          margin: 0;
          letter-spacing: -0.01em;
        }
        .cag-risk-pill {
          font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
          font-size: 11px;
          font-weight: 600;
          padding: 2px 8px;
          border-radius: 9999px;
          border: 1px solid;
          letter-spacing: 0.03em;
        }
        .cag-halted-tag {
          font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
          font-size: 10px;
          font-weight: 700;
          color: #f43f5e;
          background: rgba(244, 63, 94, 0.12);
          border: 1px solid rgba(244, 63, 94, 0.4);
          padding: 2px 7px;
          border-radius: 4px;
          letter-spacing: 0.05em;
        }
        .cag-summary {
          font-size: 13px;
          color: #8da4be;
          margin: 0;
          line-height: 1.45;
        }
        .cag-gauge-wrap {
          flex-shrink: 0;
        }
        .cag-body {
          display: flex;
          flex-direction: column;
          gap: 16px;
          margin-top: 14px;
          border-top: 1px solid #162436;
          padding-top: 16px;
        }
        .cag-section {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .cag-section-label {
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: #64748b;
        }
        .cag-normal-note {
          margin-top: 14px;
          padding: 12px 14px;
          background: #070e17;
          border: 1px dashed #1a2a3c;
          border-radius: 8px;
          font-size: 12.5px;
          color: #64748b;
        }

        /* SPR Panel */
        .cag-spr-panel {
          background: #07101a;
          border: 1px solid #15263a;
          border-radius: 10px;
          padding: 14px 16px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .cag-spr-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
        }
        .cag-spr-title {
          font-size: 13px;
          font-weight: 600;
          color: #e2e8f0;
          display: block;
        }
        .cag-spr-subtitle {
          font-size: 11px;
          color: #2dd4bf;
          font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
          margin-top: 2px;
        }
        .cag-btn-plan {
          background: rgba(45, 212, 191, 0.08);
          border: 1px solid #2dd4bf;
          color: #2dd4bf;
          padding: 5px 12px;
          border-radius: 6px;
          font-size: 11.5px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.15s ease-in-out;
        }
        .cag-btn-plan:hover {
          background: #2dd4bf;
          color: #071018;
          box-shadow: 0 0 12px rgba(45, 212, 191, 0.35);
        }
        .cag-btn-plan-active {
          background: #2dd4bf;
          color: #071018;
        }
        .cag-spr-stats {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
        }
        .cag-spr-stat-box {
          background: #0a1624;
          border: 1px solid #1a2a3c;
          border-radius: 8px;
          padding: 8px 12px;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .cag-spr-val {
          font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
          font-size: 16px;
          font-weight: 700;
          color: #2dd4bf;
        }
        .cag-spr-lbl {
          font-size: 10.5px;
          color: #8da4be;
          letter-spacing: 0.02em;
        }

        /* Drawer Schedule */
        .cag-drawer {
          margin-top: 4px;
          border-top: 1px solid #15263a;
          padding-top: 12px;
          display: flex;
          flex-direction: column;
          gap: 8px;
          animation: cagFadeIn 0.2s ease-out;
        }
        @keyframes cagFadeIn {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .cag-drawer-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 11.5px;
        }
        .cag-drawer-title {
          font-weight: 600;
          color: #cbd5e1;
        }
        .cag-drawer-meta {
          color: #8da4be;
        }
        .cag-table-scroll {
          max-height: 300px;
          overflow-y: auto;
          border: 1px solid #15263a;
          border-radius: 6px;
        }
        .cag-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 11.5px;
          background: #060d15;
        }
        .cag-table th {
          text-align: left;
          padding: 7px 10px;
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: #64748b;
          border-bottom: 1px solid #15263a;
          background: #09131e;
          position: sticky;
          top: 0;
          z-index: 1;
        }
        .cag-table td {
          padding: 6px 10px;
          border-bottom: 1px solid #0f1c2a;
          color: #cbd5e1;
        }
        .cag-table tbody tr:hover {
          background: rgba(45, 212, 191, 0.04);
        }
        .cag-mono {
          font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        }
        .cag-strong {
          font-weight: 700;
          color: #f1f5f9;
        }
        .cag-text-green {
          color: #34d399;
        }
        .cag-text-red {
          color: #f43f5e;
        }
        .cag-alert {
          background: #0b1522;
          border: 1px solid #1a2a3c;
          border-radius: 8px;
          padding: 14px;
          font-size: 12px;
          color: #8da4be;
        }
        @media (max-width: 640px) {
          .cag-spr-stats {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}