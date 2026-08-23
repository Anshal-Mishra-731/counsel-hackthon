# 🌊 Chokepoint — Frontend

Live geopolitical risk simulator for India's crude oil supply chain. Pick a source (supplier) country, run a simulation, and the map draws the shortest sea trade route to India — highlighted with a distinct dark, animated line so it's obvious which route the simulation produced. The Analytics page lets you search any source country for its full route/risk/economic breakdown, backed by live charts.

> Modelled estimates for planning discussion — not an official forecast.

---

## 🧱 Tech Stack

- **React** (Vite)
- **react-router-dom** — routing (`/`, `/dashboard`)
- **react-leaflet** + **leaflet** — interactive map, dark/light CARTO basemaps
- **recharts** — bar/pie charts across Analytics
- Plain CSS-in-JS (`<style>` blocks per component) — no external CSS framework

Backend is a separate Python (FastAPI) service the frontend talks to via `VITE_API_BASE`.

---

## 📁 Project Structure

```
counsel-hackthon/
├── backend/                          # Python FastAPI backend (separate service)
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── AlternativeSourceTable.jsx   # Alternate supplier table (lead time, offered bpd)
    │   │   ├── CorridorAnalyticsGrid.jsx    # Full per-corridor breakdown grid (Analytics page)
    │   │   ├── DetailOverlay.jsx            # Click-through corridor detail modal
    │   │   ├── EconomicPanel.jsx            # Price spike / supply drop / net gap stats
    │   │   ├── Header.jsx                   # ChokepointMark brand icon (SVG)
    │   │   ├── MapView.jsx                  # 🔄 UPDATED — map, route toggle, simulated-route animation
    │   │   ├── RiskGauge.jsx                # Semi-circular risk gauge (SVG)
    │   │   ├── RouteSearchPanel.jsx         # 🆕 NEW — Analytics search bar
    │   │   ├── Sidebar.jsx                  # 🔄 UPDATED — added "show all routes" toggle
    │   │   ├── StatsView.jsx                # 🔄 UPDATED — wires in RouteSearchPanel
    │   │   ├── SupplierTable.jsx            # Affected suppliers table (lost vs surviving bpd)
    │   │   └── SupplyFlowDiagram.jsx        # Supplier → chokepoint → India flow SVG
    │   ├── lib/
    │   │   ├── api.js                       # API client, RISK_COLORS/LABELS, slugifyCountry
    │   │   └── format.js                    # Number/barrel/bpd formatters, risk-tier helpers
    │   ├── pages/
    │   │   ├── Dashboard.jsx                # 🔄 UPDATED — wires Sidebar + MapView/StatsView
    │   │   └── Home.jsx                     # Marketing/landing page
    │   ├── App.jsx                          # Route definitions
    │   ├── main.jsx                         # App entry point
    │   └── index.css                        # Global styles / CSS variables
    ├── package.json
    └── package-lock.json
```

🔄 = updated in this pass · 🆕 = newly added. Every other file is unchanged — copy them over exactly as-is.

---

## 🔌 Backend API Contract

The frontend expects a backend at `VITE_API_BASE` (default `http://localhost:8000`) exposing:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/meta` | GET | Supplier country list (lat/lng/port) + India destination info |
| `/api/corridors` | GET | All corridors with current risk scores/buckets and waypoints |
| `/api/corridor/{key}` | GET | Full detail for one corridor (baseline, suppliers, alternates, economics) |
| `/api/route?source=X` | GET | Resolves a source country to its corridor + route waypoints |
| `/api/simulate` | POST | Re-runs the risk simulation, returns updated corridors |
| `/api/stats` | GET | Aggregate analytics: baseline demand, corridor dependency, supplier breakdown |
| `/api/analytics` | GET | Full affected/alternate/economics detail for every corridor, in one call |

> The number of corridors visible on the map/toggle/analytics is entirely driven by what `/api/corridors` and `/api/analytics` return. To show more sea lanes (Strait of Malacca, INSTC, etc.), add them to the backend's corridor dataset — the frontend automatically renders whatever it gets back.

---

## 🚀 Running the Project

### 1. Backend
```bash
cd counsel-hackthon/backend
uvicorn server:app --reload --port 8000
```

### 2. Frontend
```bash
cd counsel-hackthon/frontend
npm install
npm run dev
```

Optional `.env` in `frontend/`:
```
VITE_API_BASE=http://localhost:8000
```

Open `http://localhost:5173` — landing page at `/`, live console at `/dashboard`.

---

## ✨ What Changed in This Update

### 1. Simulated route — dark, animated highlight
Before simulating, the active route (selected source → India) is drawn as a normal risk-colored line. **After** clicking **Start Simulation**, the same route switches to a **glow-halo + dark-core** rendering:
- A blurred, breathing cyan halo underneath
- A dark (`#04070c`), dashed, marching-ants animated core line on top
- A pulsing marker at the India end

This makes it unmistakable which route the simulation produced — even against the dark CARTO basemap (the halo prevents the dark line from ever blending invisibly into the background).

The "locked" state is tracked per-source: it only shows for the exact country you just simulated, and clears automatically the moment you pick a different source — no stale/incorrect "locked" badges.

### 2. "Show all possible routes" toggle
A switch in the sidebar, left panel, under **Start Simulation**:
- **OFF (default):** only the selected/simulated source's route is drawn.
- **ON:** every corridor the backend returns is drawn as light, semi-transparent lines with clickable "buoy" markers, alongside the highlighted active route.

> Note: how many distinct corridors you see with the toggle ON depends entirely on the backend's corridor dataset — see the API note above.

### 3. Analytics — route search with charts
A new **Search a route** panel at the top of the Analytics page (`RouteSearchPanel.jsx`):
- Type or click-suggest any source country
- Instantly see: resolved route/corridor name, risk score + bucket, a plain-language suggestion, a bar chart of affected countries' lost bpd, the alternate-supplier table, the full supplier table, and the economic impact panel (price spike, supply drop, net gap)
- Fetches fresh via `/api/route` + `/api/corridor/{key}` on every search — no stale/cached-array bugs

---

## 🗺️ How the Map Behaves (summary)

| State | What's drawn |
|---|---|
| Toggle OFF, not simulated | Only the active route, normal risk color |
| Toggle OFF, simulated | Only the active route, dark glow-halo animated |
| Toggle ON, not simulated | All corridors (light) + active route (normal color) |
| Toggle ON, simulated | All corridors (light) + active route (dark glow-halo animated) |

Switching source country always resets the simulated/"locked" state for the new source.

---

## 🎨 Theming

Colors are CSS custom properties (`--bg-deep`, `--hairline`, `--accent-cyan`, `--tier-*`, etc.) set on `document.body[data-theme]`. `theme` state lives in `App.jsx`, passed to `Home` and `Dashboard`. The sidebar's 🌙/☀️ toggle switches it app-wide.

Risk bucket colors (`lib/api.js`):

| Bucket | Color |
|---|---|
| Low | `#34d399` |
| Guarded | `#fbbf24` |
| Elevated | `#fb923c` |
| High | `#fb7185` |
| Critical | `#f43f5e` |

---

## 🧩 Known Limitations / Next Steps

- Corridor count is capped by the backend dataset — extend it to surface more sea lanes.
- Per-source "spur" waypoints (source port → chokepoint) are partially synthesized on the frontend (`MapView.jsx` prepends the source's own port coordinate when it's far from the backend's first waypoint). For fully accurate shortest-path geometry per source, this should be computed and returned by the backend instead.
- `corridor_dependency` and `supplier_breakdown` charts show a "waiting on backend" note until `load_supplier_corridor_dependency()` is implemented server-side.

---

## 🏗️ Built For

Problem Statement 1 — AI-Driven Energy & Supply Chain Resilience.