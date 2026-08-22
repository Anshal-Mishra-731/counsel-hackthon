import React, { useMemo, useState } from "react";
import { RISK_COLORS, RISK_LABELS } from "../lib/api";

export default function Sidebar({
  theme, setTheme,
  view, setView,
  suppliers, destination,
  selectedSource, setSelectedSource,
  corridors, activeCorridorKey, onSelectCorridor,
  onStartSimulation, simulating,
  mode, updatedAt,
}) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!query.trim()) return suppliers;
    const q = query.toLowerCase();
    return suppliers.filter((s) => s.country.toLowerCase().includes(q));
  }, [suppliers, query]);

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <span className="sonar" />
          <div>
            <div className="brand-title">Chokepoint</div>
            <div className="brand-sub">Maritime Corridor Risk</div>
          </div>
        </div>
        <div className="theme-toggle">
          <button className={theme === "dark" ? "active" : ""} onClick={() => setTheme("dark")} title="Dark theme">🌙</button>
          <button className={theme === "light" ? "active" : ""} onClick={() => setTheme("light")} title="Light theme">☀️</button>
        </div>
      </div>

      <div className="view-toggle">
        <button className={view === "map" ? "active" : ""} onClick={() => setView("map")}>🗺 Route Map</button>
        <button className={view === "stats" ? "active" : ""} onClick={() => setView("stats")}>📊 Analytics</button>
      </div>

      <div className="field-group">
        <label className="field-label">Source · Supplier Country</label>
        <input
          className="search-input"
          placeholder="Search country…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="country-list">
          {filtered.map((s) => (
            <button
              key={s.country}
              className={`country-chip ${s.country === selectedSource ? "active" : ""}`}
              onClick={() => setSelectedSource(s.country)}
            >
              {s.country}
              <span className="country-chip-port">{s.port}</span>
            </button>
          ))}
          {filtered.length === 0 && (
            <p className="corridor-summary" style={{ padding: "8px 4px" }}>No country matches "{query}".</p>
          )}
        </div>

        <div className="swap-row">
          <div className="line" />
          <span className="swap-icon">⛴ sea route ⛴</span>
          <div className="line" />
        </div>

        <div>
          <label className="field-label">Destination</label>
          <div className="dest-box">📍 {destination.name} — {destination.port}</div>
        </div>
      </div>

      <button className="start-btn" onClick={onStartSimulation} disabled={simulating}>
        {simulating ? "Running simulation…" : "▶ Start Simulation"}
      </button>

      <div className="divider" />

      <div className="legend">
        <div className="legend-title">Risk legend</div>
        {Object.entries(RISK_LABELS).map(([key, label]) => (
          <div className="legend-row" key={key}>
            <span className="dot" style={{ background: RISK_COLORS[key] }} />
            {label}
          </div>
        ))}
      </div>

      <div className="divider" />

      <label className="field-label">Corridors</label>
      <div className="corridor-list">
        {corridors.map((c) => (
          <div
            key={c.key}
            className={`corridor-card ${c.key === activeCorridorKey ? "active" : ""}`}
            onClick={() => onSelectCorridor(c.key)}
          >
            <div className="corridor-card-top">
              <span className="corridor-name">{c.name}</span>
              <span className="risk-chip" style={{ background: RISK_COLORS[c.risk_bucket] }}>
                {c.risk_score}
              </span>
            </div>
            <div className="corridor-summary">{c.summary || "No summary available."}</div>
          </div>
        ))}
        {corridors.length === 0 && <p className="corridor-summary">No corridor data yet.</p>}
      </div>

      <div className="status-line">
        <span>mode: {mode}</span>
        <span>{updatedAt ? `updated ${new Date(updatedAt * 1000).toLocaleTimeString()}` : "—"}</span>
      </div>
    </aside>
  );
}
