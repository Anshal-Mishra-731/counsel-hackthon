# Chokepoint

A live maritime corridor risk console: pick a source and destination
country, get every plausible sea route colored by live geopolitical risk,
and drill into any route for the full backend-driven breakdown.

```
chokepoint/
├── backend/
│   ├── server.py              FastAPI app — drop next to your run.py
│   ├── requirements-api.txt   fastapi + uvicorn
│   └── README.md              step-by-step integration guide
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── .env.example
    └── src/
        ├── main.jsx, App.jsx, index.css
        ├── lib/
        │   ├── api.js          every network call the UI makes
        │   └── format.js       number/tier formatting helpers
        ├── components/
        │   ├── Sidebar.jsx      search/select source+dest, start simulation,
        │   │                    corridor list, theme + Map/Analytics toggle
        │   ├── MapView.jsx      Leaflet map, risk-colored routes, floating
        │   │                    detail buttons, full-screen toggle
        │   ├── DetailOverlay.jsx  high z-index route detail panel
        │   ├── StatsView.jsx    dataset-driven analytics charts
        │   ├── Header.jsx       brand mark (used on the landing page)
        │   └── RiskGauge.jsx, SupplyFlowDiagram.jsx, SupplierTable.jsx,
        │       AlternativeSourceTable.jsx, EconomicPanel.jsx
        │       (kept for reuse — the original per-corridor detail widgets)
        └── pages/
            ├── Home.jsx         landing page
            └── Dashboard.jsx    the console itself
```

## Run it

**Backend** — see `backend/README.md` for the two import paths to confirm,
then:
```bash
pip install -r backend/requirements-api.txt
uvicorn server:app --reload --port 8000   # run from your project root
```

**Frontend**:
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## What's new in this pass

- **Route simulator**: search a country or click a marker on the map for
  source and destination; corridors update from the live API, colored by
  the same five-bucket risk scale (`low` → `critical`) everywhere.
- **Floating detail buttons**: every route has a small buoy marker at its
  midpoint — click it (or click the route line itself) to open the detail
  overlay: affected suppliers, alternate sources with real trade volumes,
  replacement timeline.
- **`+z-index` detail page**: `DetailOverlay` renders at `z-index: 2000`
  as a slide-in panel, so it sits above the map and sidebar completely.
- **Start Simulation**: re-runs your Phase 1 → Phase 2 pipeline on demand
  (rate-limited server-side so repeated clicks can't blow your Gemini quota).
- **Analytics view**: a new sidebar toggle ("📊 Analytics") swaps the map
  for charts — corridor risk snapshot, import dependency by corridor,
  top supplier countries, baseline demand — all from `/api/stats`, which
  reads your CSVs through your own loader functions. No numbers are
  invented in the frontend.
- **Light/dark theme**: one toggle in the sidebar, every screen (including
  the map tiles, which switch between CARTO's light and dark basemaps).
- **Full screen**: a button on the map topbar calls the Fullscreen API on
  the map container.

## Design system

Space Grotesk for headings, IBM Plex Sans for body copy, IBM Plex Mono for
every number — loaded via Google Fonts in `index.html`. All colors are CSS
variables split into a dark and light set in `src/index.css`, switched by
`body[data-theme]`.
