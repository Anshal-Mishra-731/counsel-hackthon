# Chokepoint API — integration guide

`server.py` is a new file — it doesn't replace anything you already have.
It sits next to `run.py` and reuses your existing pipeline as-is.

## 1. Install

```bash
pip install -r backend/requirements-api.txt   # fastapi + uvicorn
```

(keep using whatever env already has google-generativeai, pandas, requests,
pydantic-settings etc. for your pipeline — server.py imports straight from
`src.final_pipeline`, so it needs the same environment your `run.py` uses.)

## 2. Place the file

Copy `server.py` to your **project root**, the same folder as `run.py`:

```
your-project/
├── run.py
├── server.py          <- new
├── src/
│   ├── config.py
│   ├── final_pipeline.py
│   ├── phase1.py
│   ├── phase2_engine.py
│   └── ...
└── data/
    ├── pt_import_export_combined.csv
    └── ...
```

## 3. Fix two import paths

Open `server.py` and find the two lines marked `# ADJUST THIS PATH`:

```python
from src.oil_balance import load_baseline_oil_balance
from src.corridor_dependency import load_supplier_corridor_dependency
```

Point these at wherever your two loader functions actually live. If you
leave them wrong, **nothing crashes** — `/api/stats` just reports those
two sections as `"available": false` until you fix it, so you can wire
the rest of the app up first and come back to this.

## 4. Run it

```bash
uvicorn server:app --reload --port 8000
```

On startup it:
- loads your last `final_result.json` from disk if one exists, so the API
  has real data immediately instead of an empty state
- otherwise serves a clearly-labelled `mode: "sample"` snapshot
- kicks off a background loop that calls your existing `run_once()`
  (Phase 1 → Phase 2, unmodified) every `REFRESH_INTERVAL_SECONDS`
  (pulled from your `final_pipeline.py`, same 120s default)

Point the frontend at it — copy `frontend/.env.example` to
`frontend/.env` and confirm `VITE_API_BASE=http://localhost:8000`.

## Endpoints

| Method | Path | Returns |
|---|---|---|
| GET | `/api/meta` | supplier countries (name + lat/lng) + destination (India) |
| GET | `/api/corridors` | all corridors: risk score, bucket, summary, map waypoints |
| GET | `/api/corridor/{key}` | full detail: baseline, affected suppliers, alternates, economics |
| GET | `/api/route?source=Iraq` | which corridor a given supplier country routes through |
| POST | `/api/simulate` | triggers a fresh Phase 1 → Phase 2 run (rate-limited, 15s cooldown) |
| GET | `/api/stats` | dataset-driven analytics: baseline demand, corridor dependency share, top suppliers, risk snapshot |

Every field the frontend renders — corridor cards, the map, the detail
overlay, the analytics charts — comes from one of these. Nothing about
risk scores, bpd figures, or economics is hardcoded in the frontend; it's
either live pipeline output or `/api/stats` reading straight from your
CSVs through your own loader functions.

## Static reference data (not business data)

Two small tables live in `server.py` and are the only "hardcoded" things
in the file:
- `CORRIDOR_WAYPOINTS` — approximate sea-lane polylines so the map has
  something to draw. These are cartographic geometry, not modelled output.
- `COUNTRY_COORDS` — lat/lng per supplier country, for plotting markers.

Both are keyed off the country/corridor names your pipeline already uses
(`SUPPLIER_LEAD_TIME_DAYS`, `CORRIDOR_KEY_TO_NAME`). Add a country or
corridor to your pipeline and add one line here to plot it.
