const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function req(path, options) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  meta: () => req("/api/meta"),
  corridors: () => req("/api/corridors"),
  corridorDetail: (key) => req(`/api/corridor/${key}`),
  route: (source) => req(`/api/route?source=${encodeURIComponent(source)}`),
  simulate: (scenario) =>
    req("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: scenario || "" }),
    }),
  stats: () => req("/api/stats"),
  analytics: () => req("/api/analytics"),
  reset: () =>
    req("/api/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    }),
};

// Five-bucket risk scale used across the map, sidebar and detail overlay.
export const RISK_COLORS = {
  low: "#34d399",
  guarded: "#fbbf24",
  elevated: "#fb923c",
  high: "#fb7185",
  critical: "#f43f5e",
};

export const RISK_LABELS = {
  low: "Low",
  guarded: "Guarded",
  elevated: "Elevated",
  high: "High",
  critical: "Critical",
};