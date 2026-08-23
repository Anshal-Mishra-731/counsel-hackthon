import React, { useEffect, useMemo, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, ResponsiveContainer, Cell,
} from "recharts";
import { api, RISK_COLORS, RISK_LABELS } from "../lib/api";
import RiskGauge from "./RiskGauge.jsx";
import SupplierTable from "./SupplierTable.jsx";
import AlternativeSourceTable from "./AlternativeSourceTable.jsx";
import EconomicPanel from "./EconomicPanel.jsx";

export default function RouteSearchPanel() {
  const [query, setQuery] = useState("");
  const [countries, setCountries] = useState([]);
  const [result, setResult] = useState(null); // { detail, sourceCountry }
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);

  // Sirf country-suggestion list ke liye — ye fast hai aur search ka blocker nahi hai
  useEffect(() => {
    let cancelled = false;
    api.meta()
      .then((m) => {
        if (cancelled) return;
        const list = m?.suppliers?.map((s) => s.country) || [];
        setCountries(list);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const suggestions = useMemo(() => {
    if (!query.trim()) return [];
    const q = query.toLowerCase();
    return countries.filter((c) => c.toLowerCase().includes(q)).slice(0, 6);
  }, [query, countries]);

  // Search seedha corridorDetail call karta hai jab bhi search ho — koi
  // preloaded/stale array pe depend nahi karta, isliye race condition nahi.
  async function runSearch(countryName) {
    const name = (countryName ?? query).trim();
    if (!name) return;
    setSearching(true);
    setError(null);
    setResult(null);
    try {
      const routeRes = await api.route(name);
      const corridorKey = routeRes.corridor_key;
      if (!corridorKey) {
        setError(`"${name}" ke liye koi corridor match nahi mila.`);
        return;
      }
      const detail = await api.corridorDetail(corridorKey);
      setResult({ detail, sourceCountry: name });
    } catch (e) {
      setError(`"${name}" ke liye route/analytics fetch nahi ho paya — naam check karo ya backend running hai check karo.`);
    } finally {
      setSearching(false);
    }
  }

  const suggestionText = useMemo(() => {
    if (!result) return "";
    const d = result.detail;
    const top = [...(d.alternative_sources || [])].sort(
      (a, b) => b.additional_bpd_offered - a.additional_bpd_offered
    )[0];
    if (d.risk_bucket === "low" || d.risk_bucket === "guarded") {
      return `Route abhi stable hai (risk ${d.risk_score}/100) — koi turant action ki zaroorat nahi, bas monitor karo.`;
    }
    if (!top) {
      return `Risk ${d.risk_score}/100 hai (${RISK_LABELS[d.risk_bucket]}), lekin is corridor ke liye alternate-supplier data available nahi hai.`;
    }
    return `Risk ${d.risk_score}/100 (${RISK_LABELS[d.risk_bucket]}) — sabse fast alternate ${top.supplier} hai, +${Math.round(
      top.additional_bpd_offered
    ).toLocaleString()} bpd offer kar sakta hai ${top.lead_time_days} din me. Diversification consider karo.`;
  }, [result]);

  const affectedChartData = (result?.detail.affected_suppliers || []).map((s) => ({
    name: s.country,
    lost: s.lost_bpd,
  }));

  return (
    <div className="route-search-panel">
      <div className="route-search-head">
        <h2>Search a route</h2>
        <p>Koi bhi source country search karo — route name, risk score, affected countries, alternates aur economic impact ek jagah.</p>
      </div>

      <div className="route-search-bar">
        <input
          className="search-input"
          placeholder="Source country search karo (e.g. Iraq, Saudi Arabia)…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runSearch()}
        />
        <button className="route-search-btn" onClick={() => runSearch()} disabled={searching}>
          {searching ? "Searching…" : "Search"}
        </button>
      </div>

      {suggestions.length > 0 && !result && (
        <div className="route-search-suggestions">
          {suggestions.map((c) => (
            <button key={c} className="route-search-suggestion-chip" onClick={() => { setQuery(c); runSearch(c); }}>
              {c}
            </button>
          ))}
        </div>
      )}

      {error && <div className="note-box">{error}</div>}

      {result && (
        <div className="route-search-result">
          <div className="route-search-result-head">
            <div>
              <div className="route-search-result-eyebrow">{result.sourceCountry} → India</div>
              <h3>{result.detail.name}</h3>
              <span className="mono" style={{ color: RISK_COLORS[result.detail.risk_bucket] }}>
                {RISK_LABELS[result.detail.risk_bucket]} · {result.detail.risk_score}/100
                {result.detail.traffic_halted ? " · traffic halted" : ""}
              </span>
            </div>
            <RiskGauge severity={(result.detail.risk_score || 0) / 100} size={92} />
          </div>

          <p className="route-search-summary">{result.detail.summary}</p>
          <div className="route-search-suggestion-box">💡 {suggestionText}</div>

          <div className="chart-grid">
            <div className="chart-card">
              <h3>Affected countries — lost bpd</h3>
              {affectedChartData.length ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={affectedChartData} margin={{ left: 4, right: 12 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--hairline)" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 10.5, fill: "var(--text-muted)" }} interval={0} angle={-30} textAnchor="end" height={60} />
                    <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
                    <RTooltip contentStyle={{ background: "var(--bg-panel)", border: "1px solid var(--hairline)", borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="lost" radius={[6, 6, 0, 0]}>
                      {affectedChartData.map((_, i) => (
                        <Cell key={i} fill={RISK_COLORS[result.detail.risk_bucket] || "#fb7185"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="note-box">No affected-supplier data for this corridor.</div>
              )}
            </div>
            <div className="chart-card">
              <h3>Alternate suppliers offered</h3>
              <AlternativeSourceTable sources={result.detail.alternative_sources} />
            </div>
          </div>

          <h4>Affected suppliers detail</h4>
          <SupplierTable suppliers={result.detail.affected_suppliers} />

          {result.detail.economic_estimates && result.detail.supply_impact && (
            <>
              <h4>Economic impact</h4>
              <EconomicPanel economics={result.detail.economic_estimates} supplyImpact={result.detail.supply_impact} />
            </>
          )}

          {!result.detail.economic_estimates && result.detail.note && (
            <div className="note-box">{result.detail.note}</div>
          )}
        </div>
      )}

      <style>{`
        .route-search-panel { display: flex; flex-direction: column; gap: 14px; margin-bottom: 24px; }
        .route-search-head h2 { margin: 0 0 4px; }
        .route-search-head p { margin: 0; font-size: 12.5px; color: var(--text-muted); }
        .route-search-bar { display: flex; gap: 8px; }
        .route-search-bar .search-input { flex: 1; }
        .route-search-btn {
          padding: 0 18px; border-radius: var(--radius-sm, 8px); border: 1px solid var(--accent-cyan);
          background: var(--accent-cyan-dim); color: var(--text-primary); font-weight: 600; cursor: pointer;
        }
        .route-search-btn:hover { background: var(--accent-cyan); color: var(--ink-900); }
        .route-search-suggestions { display: flex; gap: 6px; flex-wrap: wrap; }
        .route-search-suggestion-chip {
          padding: 5px 12px; border-radius: 999px; border: 1px solid var(--hairline-strong);
          background: var(--bg-panel-2, var(--ink-700)); color: var(--text-secondary); font-size: 12px; cursor: pointer;
        }
        .route-search-suggestion-chip:hover { border-color: var(--accent-cyan); color: var(--text-primary); }
        .route-search-result {
          background: var(--bg-panel, var(--ink-800)); border: 1px solid var(--hairline-strong);
          border-radius: 14px; padding: 20px; display: flex; flex-direction: column; gap: 12px;
        }
        .route-search-result-head { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
        .route-search-result-eyebrow { font-size: 11px; letter-spacing: 0.06em; color: var(--text-muted); text-transform: uppercase; }
        .route-search-summary { margin: 0; font-size: 13px; color: var(--text-secondary); }
        .route-search-suggestion-box {
          padding: 12px 14px; border-radius: 10px; background: var(--accent-cyan-dim, rgba(55,201,224,0.1));
          border: 1px solid var(--accent-cyan); font-size: 12.5px; color: var(--text-primary); line-height: 1.6;
        }
      `}</style>
    </div>
  );
}