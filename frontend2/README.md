# Chokepoint — India Crude Supply Risk Monitor (Frontend)

A dashboard that visualizes your Phase 1 (geopolitical risk) + Phase 2
(disruption simulation) backend output.

## Run it

```bash
npm install
npm run dev
```

Opens at `http://localhost:5173`. It boots with realistic **sample data**
baked in, so the UI works immediately even before your backend is wired up.

## Connect it to your live backend

Right now `final_pipeline.py` prints to console and writes `final_result.json`
to disk, but there's no HTTP endpoint yet for the browser to fetch. Add this
tiny FastAPI wrapper (`src/api_server.py`) to your backend project:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.final_pipeline import run_once

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

latest_result = {}

@app.get("/api/latest")
def get_latest():
    return latest_result

@app.on_event("startup")
async def startup():
    global latest_result
    latest_result = run_once()
```

Run it with:
```bash
pip install fastapi uvicorn --break-system-packages
uvicorn src.api_server:app --reload --port 8000
```

Then in the frontend, create a `.env` file:
```
VITE_API_URL=http://localhost:8000/api/latest
```

The dashboard polls this URL every 20 seconds (matching your backend's
refresh interval) and switches its status indicator from `SAMPLE DATA` to
`LIVE` automatically once it gets a real response.

## Project structure

```
frontend/
├── index.html
├── package.json
├── vite.config.js
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── index.css              ← design tokens (colors, type, spacing)
    ├── data/sampleData.js       ← fallback demo data (matches backend shape exactly)
    ├── hooks/usePipelineData.js ← fetch + 20s polling logic
    ├── lib/format.js            ← number formatting + severity-tier helpers
    └── components/
        ├── Header.jsx
        ├── RiskGauge.jsx             ← per-corridor severity arc
        ├── SupplyFlowDiagram.jsx     ← signature element (animated chokepoint)
        ├── SupplierTable.jsx
        ├── AlternativeSourceTable.jsx
        ├── EconomicPanel.jsx
        └── CorridorCard.jsx          ← combines everything per corridor
```