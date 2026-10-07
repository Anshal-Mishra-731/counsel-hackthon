import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { api, RISK_COLORS } from "../lib/api";
import CorridorAnalyticsGrid from "./CorridorAnalyticsGrid.jsx";

const PIE_COLORS = ["#37c9e0", "#f2b134", "#ff8a3d", "#2dd9b5", "#8b7bd8", "#ff4d5e", "#4fb0ff"];

function fmt(n) {
  if (n === undefined || n === null || Number.isNaN(n)) return "—";
  return Math.round(n).toLocaleString();
}

function avg(nums) {
  if (!nums || !nums.length) return 0;
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
    background: "var(--bg-panel, #0b1522)",
    border: "1px solid var(--hairline, #1e293b)",
    borderRadius: 8,
    padding: "8px 12px",
    fontSize: 12,
    color: "var(--text-primary, #f8fafc)",
  };
}

function StatCard({ label, value }) {
  return (
    <div className="stats-card">
      <div className="val mono">{value}</div>
      <div className="lbl">{label}</div>
    </div>
  );
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

  const baseline = stats.baseline || {};
  const corridor_dependency = stats.corridor_dependency || {};
  const supplier_breakdown = stats.supplier_breakdown || {};
  const corridor_risk_snapshot = stats.corridor_risk_snapshot || [];
  const mode = stats.mode || "live_monitoring";
  const updated_at = stats.updated_at;

  const riskChartData = corridor_risk_snapshot.map((c) => ({
    name: c.name?.length > 16 ? c.name.slice(0, 15) + "…" : (c.name || "Unknown"),
    risk: c.risk_score || 0,
    fill: RISK_COLORS[bucketFor(c.risk_score || 0)] || "#8ba3ba",
  }));

  const dependencyPieData = corridor_dependency.available && Array.isArray(corridor_dependency.rows)
    ? corridor_dependency.rows.map((r) => ({
        name: r.primary_corridor,
        value: Math.round((r.share_of_imports || 0) * 1000) / 10,
      }))
    : [];

  const supplierBarData = supplier_breakdown.available && Array.isArray(supplier_breakdown.rows)
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

      <div className="stats-cards">
        <StatCard label="Corridors evaluated" value={corridor_risk_snapshot.length} />
        <StatCard label="Avg. risk score" value={avg(corridor_risk_snapshot.map((c) => c.risk_score)).toFixed(0)} />
        {baseline.available && (
          <>
            <StatCard label="Avg. daily import (all years)" value={fmt(baseline.avg_all_years_bpd) + " bpd"} />
            <StatCard label={`Latest year (${baseline.latest_year || "Current"}) avg bpd`} value={fmt(baseline.latest_year_bpd)} />
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
              <Tooltip cursor={false} contentStyle={tooltipStyle()} />
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
                <Pie 
                  data={dependencyPieData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2}
                >
                  {dependencyPieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0];
                      return (
                        <div style={tooltipStyle()}>
                          <div style={{ color: "var(--text-secondary, #8ba3ba)", marginBottom: 2 }}>
                            {data.name}
                          </div>
                          <div style={{ color: "var(--accent-cyan, #2dd4bf)", fontWeight: 700, fontFamily: "monospace" }}>
                            {data.value}%
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
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
              <Tooltip cursor={false} contentStyle={tooltipStyle()} formatter={(v) => `${v}%`} />
              <Bar dataKey="share" fill="var(--accent-cyan)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="note-box">No supplier-breakdown data available yet.</div>
        )}
      </div>

      <div className="stats-header" style={{ marginTop: 28 }}>
        <h2>Full corridor breakdown</h2>
        <p>Every corridor's affected suppliers, alternate routes and economic impact — all from <span className="mono">/api/analytics</span>.</p>
      </div>
      <CorridorAnalyticsGrid />
    </div>
  );
}