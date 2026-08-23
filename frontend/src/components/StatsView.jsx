import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip as RTooltip, ResponsiveContainer, Legend,
} from "recharts";
import { api, RISK_COLORS } from "../lib/api";
import CorridorAnalyticsGrid from "./CorridorAnalyticsGrid.jsx";
import RouteSearchPanel from "./RouteSearchPanel.jsx";

const PIE_COLORS = ["#37c9e0", "#f2b134", "#ff8a3d", "#2dd9b5", "#8b7bd8", "#ff4d5e", "#4fb0ff"];

function fmt(n) {
  if (n === undefined || n === null || Number.isNaN(n)) return "—";
  return Math.round(n).toLocaleString();
}

export default function StatsView() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api.stats()
      .then((d) => !cancelled && setStats(d))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, []);

  if (loading) return <div className="stats-view"><div className="note-box">Loading analytics from /api/stats…</div></div>;
  if (error) return <div className="stats-view"><div className="note-box">Couldn't reach the backend: {error}</div></div>;
  if (!stats) return null;

  const { baseline, corridor_dependency, supplier_breakdown, corridor_risk_snapshot, mode, updated_at } = stats;

  const riskChartData = corridor_risk_snapshot.map((c) => ({
    name: c.name.length > 16 ? c.name.slice(0, 15) + "…" : c.name,
    risk: c.risk_score,
    fill: RISK_COLORS[bucketFor(c.risk_score)],
  }));

  const dependencyPieData = corridor_dependency.available
    ? corridor_dependency.rows.map((r) => ({
        name: r.primary_corridor,
        value: Math.round((r.share_of_imports || 0) * 1000) / 10,
      }))
    : [];

  const supplierBarData = supplier_breakdown.available
    ? supplier_breakdown.rows.map((r) => ({
        name: r.supplier_country,
        share: Math.round((r.share_of_imports || 0) * 1000) / 10,
      }))
    : [];

  return (
    <div className="stats-view">
      <div className="stats-header">
        <h2>Analytics</h2>
        <p>
          Live from your dataset via <span className="mono">/api/stats</span> — mode: {mode}
          {updated_at ? ` · updated ${new Date(updated_at * 1000).toLocaleTimeString()}` : ""}
        </p>
      </div>

      <RouteSearchPanel />

      <div className="stats-cards">
        <StatCard label="Corridors evaluated" value={corridor_risk_snapshot.length} />
        <StatCard label="Avg. risk score" value={avg(corridor_risk_snapshot.map((c) => c.risk_score)).toFixed(0)} />
        {baseline.available && (
          <>
            <StatCard label="Avg. daily import (all years)" value={fmt(baseline.avg_all_years_bpd) + " bpd"} />
            <StatCard label={`Latest year (${baseline.latest_year}) avg bpd`} value={fmt(baseline.latest_year_bpd)} />
          </>
        )}
      </div>

      <div className="chart-grid">
        <div className="chart-card">
          <h3>Corridor risk snapshot</h3>
          <p className="chart-sub">Current Phase-1 risk score per corridor (0–100), from the live pipeline.</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={riskChartData} layout="vertical" margin={{ left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--hairline)" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: "var(--text-muted)" }} />
              <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 11.5, fill: "var(--text-secondary)" }} />
              <RTooltip contentStyle={tooltipStyle()} />
              <Bar dataKey="risk" radius={[0, 6, 6, 0]}>
                {riskChartData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Import dependency by corridor</h3>
          <p className="chart-sub">
            {corridor_dependency.available
              ? "Share of India's crude imports routed through each corridor."
              : "Waiting on load_supplier_corridor_dependency() to be wired up on the backend."}
          </p>
          {corridor_dependency.available ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={dependencyPieData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2}>
                  {dependencyPieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <RTooltip contentStyle={tooltipStyle()} formatter={(v) => `${v}%`} />
                <Legend wrapperStyle={{ fontSize: 11.5 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="note-box">No corridor-dependency data available yet.</div>
          )}
        </div>
      </div>

      <div className="chart-card">
        <h3>Top supplier countries</h3>
        <p className="chart-sub">
          {supplier_breakdown.available
            ? "Share of India's crude imports by supplier country, most recent year."
            : "Waiting on load_supplier_corridor_dependency() to be wired up on the backend."}
        </p>
        {supplier_breakdown.available ? (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={supplierBarData} margin={{ left: 4, right: 12 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--hairline)" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 10.5, fill: "var(--text-muted)" }} interval={0} angle={-35} textAnchor="end" height={70} />
              <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} unit="%" />
              <RTooltip contentStyle={tooltipStyle()} formatter={(v) => `${v}%`} />
              <Bar dataKey="share" fill="var(--accent-cyan)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="note-box">No supplier-breakdown data available yet.</div>
        )}
      </div>

      {/* Full per-corridor breakdown: affected suppliers, alternate sources,
          risk gauge and economics for EVERY corridor, in one place. */}
      <div className="stats-header" style={{ marginTop: 28 }}>
        <h2>Full corridor breakdown</h2>
        <p>Every corridor's affected suppliers, alternate routes and economic impact — all from <span className="mono">/api/analytics</span>.</p>
      </div>
      <CorridorAnalyticsGrid />
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="stats-card">
      <div className="val mono">{value}</div>
      <div className="lbl">{label}</div>
    </div>
  );
}

function avg(nums) {
  if (!nums.length) return 0;
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}

function bucketFor(score) {
  if (score >= 80) return "critical";
  if (score >= 60) return "high";
  if (score >= 40) return "elevated";
  if (score >= 20) return "guarded";
  return "low";
}

function tooltipStyle() {
  return {
    background: "var(--bg-panel)",
    border: "1px solid var(--hairline)",
    borderRadius: 8,
    fontSize: 12,
    color: "var(--text-primary)",
  };
}