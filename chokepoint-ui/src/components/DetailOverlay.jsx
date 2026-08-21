import React, { useEffect, useState } from "react";
import { api, RISK_COLORS, RISK_LABELS } from "../lib/api";

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
              }}
            >
              <div>
                <div
                  className="risk-banner-label"
                  style={{ color: RISK_COLORS[detail.risk_bucket] }}
                >
                  {RISK_LABELS[detail.risk_bucket]} risk
                  {detail.traffic_halted ? " · traffic halted" : ""}
                </div>
                <div
                  className="risk-banner-score"
                  style={{ color: RISK_COLORS[detail.risk_bucket] }}
                >
                  {detail.risk_score}
                  <span style={{ fontSize: 13, opacity: 0.6 }}>/100</span>
                </div>
              </div>
              <div className="risk-banner-summary">{detail.summary}</div>
            </div>

            {detail.baseline && (
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
            )}

            <div className="section-title">Affected countries / suppliers</div>
            {detail.affected_suppliers?.length ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Country</th>
                    <th className="num">Normal bpd</th>
                    <th className="num">Lost bpd</th>
                    <th className="num">Surviving bpd</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.affected_suppliers.map((s) => (
                    <tr key={s.country}>
                      <td>{s.country}</td>
                      <td className="num">{fmt(s.normal_bpd)}</td>
                      <td className="num neg">−{fmt(s.lost_bpd)}</td>
                      <td className="num">{fmt(s.surviving_bpd)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="note-box">{detail.note || "No affected-supplier data for this corridor."}</div>
            )}

            <div className="section-title">Alternate routes / suppliers</div>
            {detail.alternative_sources?.length ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Supplier</th>
                    <th>Corridor</th>
                    <th className="num">Extra bpd offered</th>
                    <th className="num">Lead time (d)</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.alternative_sources.map((s) => (
                    <tr key={s.supplier}>
                      <td>{s.supplier}</td>
                      <td>{s.corridor}</td>
                      <td className="num pos">+{fmt(s.additional_bpd_offered)}</td>
                      <td className="num">{s.lead_time_days}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="note-box">No alternate-supply data available for this corridor.</div>
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
          </>
        )}
      </div>
    </div>
  );
}
