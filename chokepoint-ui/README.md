# Chokepoint — India Crude Supply Risk Console

A live geopolitical-risk radar and disruption-rerouting console for Problem
Statement 1 (AI-Driven Energy Supply Chain Resilience for Import-Dependent
Economies). Ships with a landing page, a live corridor map ("digital twin"),
a client-side what-if simulator, and the original per-corridor
supplier/alternative-source/economic breakdown.

## Run it

```bash
npm install
npm run dev
```

Opens at `http://localhost:5173`. Without a backend running, every page
renders from the bundled `sampleData.js` so the UI is fully demoable on its
own.

## Wire up your backend

`src/lib/usePipelineData.js` polls one URL every 20s and expects it to return
**exactly** the JSON shape `final_pipeline.py` already produces:

```json
{
  "phase1_risk_report": { "...": "..." },
  "phase2_disruption_report": {
    "baseline_year": "2025-26",
    "india_total_import_bpd": 4931790,
    "corridors": { "...": "..." }
  }
}
```

Point it at your API with an env var (create `.env`):

```
VITE_API_URL=http://localhost:8000/api/latest
```

A minimal FastAPI shim that just serves your last `final_result.json` with
CORS enabled is enough:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/latest")
def latest():
    with open("final_result.json") as f:
        return json.load(f)
```

The header shows a **LIVE** pulse the moment a real response comes back, and
falls back to **SAMPLE DATA** silently if the backend isn't reachable yet.

## Folder structure

```
chokepoint-ui/
├── index.html                    Vite entry, font loading, favicon
├── package.json
├── vite.config.js
├── .gitignore
├── README.md
└── src/
    ├── main.jsx                  React root + BrowserRouter
    ├── App.jsx                   Routes: "/" -> Home, "/dashboard" -> Dashboard
    ├── index.css                 Design tokens, resets, base type
    │
    ├── lib/
    │   ├── format.js             Number/bpd/barrel formatting, tier lookup
    │   ├── sampleData.js         Fallback data — exact backend contract shape
    │   ├── usePipelineData.js    Polls VITE_API_URL, falls back to sampleData
    │   ├── worldMapData.js       Auto-generated real coastline path +
    │   │                         projected marker coordinates (see below)
    │   └── simulate.js           Client-side what-if math for the simulator
    │
    ├── components/
    │   ├── Header.jsx            Dashboard top bar + ChokepointMark logo
    │   ├── WorldMap.jsx          Interactive digital-twin map
    │   ├── SimulationPanel.jsx   Severity slider + live recalculated readouts
    │   ├── CorridorCard.jsx      Expandable per-corridor report card
    │   ├── RiskGauge.jsx         Semi-circular severity gauge
    │   ├── SupplyFlowDiagram.jsx Origin → chokepoint → India flow glyph
    │   ├── SupplierTable.jsx     Affected-supplier bar table
    │   ├── AlternativeSourceTable.jsx  Ranked alternative sources
    │   └── EconomicPanel.jsx     Price spike / supply drop / net gap
    │
    └── pages/
        ├── Home.jsx               Landing page: hero radar, stats, pipeline,
        │                          capability roadmap, CTA
        └── Dashboard.jsx          The operational console (map, simulator,
                                   corridor grid) — everything from the
                                   original build, reorganised into sections
```

## About `worldMapData.js`

The map is a **real** projection, not a decorative sketch: it's generated
once from Natural Earth 110m land geometry (via `d3-geo` + `topojson-client`,
Mercator, centered on the Indian Ocean rim) and checked into
`src/lib/worldMapData.js` as a static path string + a lookup of projected
`[x, y]` coordinates for every place the corridor data references. Nothing
at runtime depends on `d3-geo` — it's a build-time generation step only, so
the shipped bundle stays small. If you ever need to change the projection or
add new points, the generator script (two dependencies, ~40 lines) is worth
recreating; it isn't checked in here to keep the deliverable to app code.

## Design system

Dark "situation room" identity: `--ink-900…600` for depth, a cyan accent for
live signal, and a four-step tier scale (`--tier-safe` → `--tier-critical`)
that reads consistently across the gauge, the map markers and the flow
diagrams. Space Grotesk carries headings, IBM Plex Sans is body copy, IBM
Plex Mono renders every number — all loaded from Google Fonts in
`index.html`. Tokens live at the top of `src/index.css`.
