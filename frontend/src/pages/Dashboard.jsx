import React, { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar.jsx";
import MapView from "../components/MapView.jsx";
import StatsView from "../components/StatsView.jsx";
import DetailOverlay from "../components/DetailOverlay.jsx";
import { api } from "../lib/api";

export default function Dashboard({ theme, setTheme }) {
  const [view, setView] = useState("map"); // "map" | "stats"
  const [meta, setMeta] = useState(null);
  const [corridors, setCorridors] = useState([]);
  const [mode, setMode] = useState("uninitialized");
  const [updatedAt, setUpdatedAt] = useState(null);
  const [selectedSource, setSelectedSource] = useState(null);
  const [activeCorridorKey, setActiveCorridorKey] = useState(null);
  const [activeRoute, setActiveRoute] = useState(null);
  const [openDetailKey, setOpenDetailKey] = useState(null);
  const [simulating, setSimulating] = useState(false);

  // Full-page blocking error — ONLY for "can't reach the backend at all"
  // situations (initial /api/meta or /api/corridors load failing).
  const [error, setError] = useState(null);

  // Small non-blocking banner — for recoverable issues like "simulation
  // succeeded but this source's route couldn't be resolved". Never blocks
  // the rest of the dashboard.
  const [routeWarning, setRouteWarning] = useState(null);

  // Sidebar toggle: OFF (default) = sirf selected/simulated route dikhega,
  // ON = sabhi possible corridors dikhenge.
  const [showAllRoutes, setShowAllRoutes] = useState(false);

  // Tracks WHICH source was last SUCCESSFULLY simulated (not a plain
  // boolean, and only set when the route actually resolved) — so the
  // "locked" badge and the visible route line can never go out of sync.
  const [simulatedSource, setSimulatedSource] = useState(null);
  const hasSimulated = Boolean(selectedSource) && simulatedSource === selectedSource;

  useEffect(() => {
    api
      .meta()
      .then((m) => {
        setMeta(m);
        setSelectedSource(m.suppliers[0]?.country ?? null);
      })
      .catch((e) => setError(e.message));
    loadCorridors();
  }, []);

  useEffect(() => {
    if (!selectedSource || !meta) return;
    api
      .route(selectedSource)
      .then((r) => {
        setActiveCorridorKey(r.corridor_key);
        setActiveRoute(r);
      })
      .catch(() => {
        setActiveRoute(null);
      });
  }, [selectedSource, meta]);

  function loadCorridors() {
    return api
      .corridors()
      .then((data) => {
        setCorridors(data.corridors);
        setMode(data.mode);
        setUpdatedAt(data.updated_at);
      })
      .catch((e) => setError(e.message));
  }

  async function handleStartSimulation() {
    setSimulating(true);
    setRouteWarning(null);
    try {
      const data = await api.simulate();
      setCorridors(data.corridors);
      setMode(data.mode);
      setUpdatedAt(data.updated_at);

      let routeOk = false;
      if (selectedSource) {
        try {
          const r = await api.route(selectedSource);
          if (r?.waypoints?.length > 1) {
            setActiveCorridorKey(r.corridor_key);
            setActiveRoute(r);
            routeOk = true;
          }
        } catch (routeErr) {
          console.error("Route refetch after simulate failed:", routeErr);
        }
      }

      // "Locked" badge only ever turns on when the route actually resolved —
      // badge and visible line can never disagree with each other.
      if (routeOk) {
        setSimulatedSource(selectedSource);
      } else {
        setSimulatedSource(null);
        setRouteWarning(
          `Simulation ho gaya, lekin "${selectedSource}" ka route resolve nahi hua. Backend /api/route check karo.`
        );
      }
    } catch (e) {
      // Only a genuine /api/simulate failure lands here — not a route hiccup.
      setError(e.message);
    } finally {
      setSimulating(false);
    }
  }

  if (error) {
    return (
      <div className="app">
        <div className="app-error">
          <p>Can't reach the API at the configured VITE_API_BASE.</p>
          <p className="mono">{error}</p>
          <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Start the backend with <span className="mono">uvicorn server:app --reload --port 8000</span>
          </p>
        </div>
      </div>
    );
  }

  if (!meta) {
    return (
      <div className="app">
        <div className="app-loading">Loading dashboard…</div>
      </div>
    );
  }

  return (
    <div className="app">
      {routeWarning && (
        <div
          style={{
            position: "fixed",
            top: 12,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 9999,
            background: "#3a1a1a",
            border: "1px solid #f43f5e",
            color: "#fecaca",
            padding: "10px 18px",
            borderRadius: 10,
            fontSize: 13,
            maxWidth: "90%",
            textAlign: "center",
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
          }}
        >
          ⚠️ {routeWarning}
          <button
            onClick={() => setRouteWarning(null)}
            style={{
              marginLeft: 12,
              background: "none",
              border: "none",
              color: "#fecaca",
              cursor: "pointer",
              fontWeight: 700,
            }}
          >
            ✕
          </button>
        </div>
      )}

      <Sidebar
        theme={theme}
        setTheme={setTheme}
        view={view}
        setView={setView}
        suppliers={meta.suppliers}
        destination={meta.destination}
        selectedSource={selectedSource}
        setSelectedSource={setSelectedSource}
        corridors={corridors}
        activeCorridorKey={activeCorridorKey}
        onSelectCorridor={(key) => setActiveCorridorKey(key)}
        onStartSimulation={handleStartSimulation}
        simulating={simulating}
        mode={mode}
        updatedAt={updatedAt}
        showAllRoutes={showAllRoutes}
        onToggleShowAllRoutes={setShowAllRoutes}
      />

      {view === "map" ? (
        <MapView
          theme={theme}
          corridors={corridors}
          activeCorridorKey={activeCorridorKey}
          activeRoute={activeRoute}
          onOpenDetail={setOpenDetailKey}
          destination={meta.destination}
          suppliers={meta.suppliers}
          selectedSource={selectedSource}
          setSelectedSource={setSelectedSource}
          showAllRoutes={showAllRoutes}
          hasSimulated={hasSimulated}
        />
      ) : (
        <StatsView />
      )}

      {openDetailKey && (
        <DetailOverlay corridorKey={openDetailKey} onClose={() => setOpenDetailKey(null)} />
      )}
    </div>
  );
}