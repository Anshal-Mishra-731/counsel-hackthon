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
  const [error, setError] = useState(null);

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

  // NEW: Accepts customScenario from the Sidebar text box
  async function handleStartSimulation(customScenario = "") {
    setSimulating(true);
    try {
      const data = await api.simulate(customScenario);
      setCorridors(data.corridors);
      setMode(data.mode);
      setUpdatedAt(data.updated_at);
      // refresh the active route too so its risk color/summary stays in sync
      if (selectedSource) {
        api.route(selectedSource).then(setActiveRoute).catch(() => {});
      }
    } catch (e) {
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