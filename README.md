# Chokepoint: AI-Driven Energy & Supply Chain Resilience

Chokepoint is a live geopolitical risk simulator and analytical dashboard engineered to safeguard India's crude oil supply chain. By synthesizing real-time global intelligence, the platform models disruptions across critical maritime corridors, calculates economic impacts, reallocates procurement routes, and optimizes Strategic Petroleum Reserve (SPR) drawdowns.

This repository contains both the Python-based analytical engine and the React-based interactive visualization layer.

---

## Technologies Used

The architecture is fully decoupled, utilizing a high-performance backend to handle intensive LLM computations and a reactive frontend for real-time geographic visualization.

* **Backend Ecosystem:** Python 3.10+, FastAPI, Uvicorn (ASGI server), Pydantic (data validation).
* **AI & Data Ingestion:** Google Gemini LLM API (intelligence parsing), RSS Feeds (live breaking news), Finnhub API (financial and flight data endpoints).
* **Frontend Ecosystem:** Node.js, npm, React (Vite build tool).
* **Visualization & UI:** React-Router-DOM (routing), React-Leaflet & Leaflet.js (interactive geographic mapping with CARTO basemaps), Recharts (data visualization), custom CSS-in-JS.

---

## Core Features & Analytical Pipeline

### 1. Live Intelligence & Risk Agent

The backend ingests live data streams via RSS news feeds and Finnhub endpoints. A dedicated Gemini LLM agent continuously parses this unstructured data to assess global geopolitical stability. It assigns real-time risk scores (0-100) and traffic statuses to six major maritime chokepoints, including the Strait of Hormuz, Red Sea, and Strait of Malacca.

### 2. Interactive "What-If" Sandbox

Designed for live demonstrations, the platform allows users to inject custom hypothetical scenarios (e.g., "A submarine blockade in the Strait of Malacca") into the simulation. The backend intercepts this text, overrides the live news feed, and forces the LLM to treat the scenario as absolute truth, instantly cascading the effects throughout the UI.

### 3. Smart Caching System

To prevent LLM API rate-limiting during testing and ensure instantaneous frontend load times, the backend utilizes an in-memory caching mechanism. The cache holds recent calculations but is intentionally bypassed and wiped clean whenever a user executes a new simulation, ensuring the data is always mathematically fresh when needed.

### 4. Economic Disruption Simulator

When a corridor's risk exceeds critical thresholds, the engine calculates the exact barrel shortfall. It models anticipated crude price spikes using a 1.25x price elasticity assumption and evaluates the net gap against India's total baseline demand.

### 5. Procurement Optimization

The system dynamically reroutes halted shipments to alternative sea lanes. For instance, if the Red Sea is compromised, Russian crude is automatically reallocated via the Cape of Good Hope or the Chennai-Vladivostok Maritime Corridor (CVMC), recalculating the transit lead times accordingly.

### 6. Phase 4 SPR Optimization

A granular model that calculates the exact daily drawdown required from India's Strategic Petroleum Reserves (ISPRL). It allocates emergency barrel drawdowns across specific underground caverns (Padur, Mangaluru, Visakhapatnam) and OMC commercial reserves to cover the supply gap until alternative shipments arrive.

### 7. Dynamic Route Visualization

Sea routes are rendered using high-precision geographical coordinate arrays. Simulated active routes are highlighted using a dark-core, dashed, marching-ants animation positioned over a glowing cyan halo, ensuring maximum visibility against the dark CARTO basemap.

---

## Setup and Installation

Follow these instructions to run the full application locally.

### Backend Setup (FastAPI)

1. **Clone the repository and navigate to the backend:**
```bash
git clone <repository_url>
cd counsel/backend

```


2. **Create and activate a virtual environment:**
* Windows: `python -m venv venv` followed by `venv\Scripts\activate`
* macOS/Linux: `python3 -m venv venv` followed by `source venv/bin/activate`


3. **Install the required Python packages:**
```bash
pip install -r requirements.txt

```


4. **Configure Environment Variables:**
Create a `.env` file in the `backend` directory and add your API keys (Google Gemini, Finnhub, etc.).
5. **Start the ASGI server:**
```bash
uvicorn src.main:app --reload --port 8000

```



### Frontend Setup (React/Vite)

1. **Navigate to the frontend directory:**
```bash
cd counsel/frontend

```


2. **Install Node dependencies:**
```bash
npm install

```


3. **Configure Environment Variables:**
Create a `.env` file in the `frontend` directory and point it to the local backend:
```env
VITE_API_BASE=http://localhost:8000

```


4. **Start the development server:**
```bash
npm run dev

```


5. **View the application:**
Open `http://localhost:5173` in your web browser.

---

## API Architecture

The frontend communicates with the FastAPI backend via the following primary endpoints:

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/meta` | GET | Supplier country list (lat/lng/port) and destination info |
| `/api/corridors` | GET | High-level status and waypoints for all corridors |
| `/api/corridor/{key}` | GET | Deep-dive intelligence, economics, and SPR resolution |
| `/api/route?source=X` | GET | Resolves a source country to its specific corridor |
| `/api/simulate` | POST | Wipes cache and executes a fresh live simulation |
| `/api/stats` | GET | Aggregate analytics and dependency metrics |
| `/api/analytics` | GET | Full affected/alternate detail for the analytics grid |

---

## Directory Structure

```text
counsel/
├── backend/
│   ├── data/
│   ├── src/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── schemas.py
│   │   │   └── services.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── disruption_sim.py
│   │   │   ├── procurement_opt.py
│   │   │   ├── risk_agent.py
│   │   │   └── spr_optimizer.py
│   │   ├── config.py
│   │   └── main.py
│   ├── venv/
│   ├── .env
│   └── requirements.txt
│
└── frontend/
    ├── node_modules/
    ├── src/
    │   ├── components/
    │   │   ├── AlternativeSourceTable.jsx
    │   │   ├── CorridorAnalyticsGrid.jsx
    │   │   ├── DetailOverlay.jsx
    │   │   ├── EconomicPanel.jsx
    │   │   ├── Header.jsx
    │   │   ├── MapView.jsx
    │   │   ├── RiskGauge.jsx
    │   │   ├── RouteSearchPanel.jsx
    │   │   ├── Sidebar.jsx
    │   │   ├── StatsView.jsx
    │   │   ├── SupplierTable.jsx
    │   │   └── SupplyFlowDiagram.jsx
    │   ├── lib/
    │   │   ├── api.js
    │   │   └── format.js         
    │   ├── pages/
    │   │   ├── Dashboard.jsx
    │   │   └── Home.jsx
    │   ├── App.jsx
    │   ├── index.css
    │   └── main.jsx
    ├── .env
    ├── index.html
    ├── package-lock.json
    ├── package.json
    └── vite.config.js

```

---

To ensure this documentation is fully complete before you submit it, could you clarify what Phase 5 of the hackathon project entails, so I can accurately add its details to the core features section?