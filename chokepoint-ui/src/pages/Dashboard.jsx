import React, { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar.jsx";
import MapView from "../components/MapView.jsx";
import DetailOverlay from "../components/DetailOverlay.jsx";
import { api } from "../lib/api";

export default function Dashboard() {
  const [theme, setTheme] = useState("dark");
  const [meta, setMeta] = useState(null);
  const [corridors, setCorridors] = useState([]);
  const [mode, setMode] = useState("uninitialized");
  const [updatedAt, setUpdatedAt] = useState(null);
  const [selectedSource, setSelectedSource] = useState(null);
  const [activeCorridorKey, setActiveCorridorKey] = useState(null);
  const [openDetailKey, setOpenDetailKey] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.meta()
      .then((m) => {
        setMeta(m);
        setSelectedSource(m.suppliers[0]?.country ?? null);
      })
      .catch((e) => setError(e.message));
    loadCorridors();
  }, []);

  useEffect(() => {
    if (!selectedSource || !meta) return;
    api.route(selectedSource)
      .then((r) => setActiveCorridorKey(r.corridor_key))
      .catch(() => {});
  }, [selectedSource, meta]);

  function loadCorridors() {
    return api.corridors()
      .then((data) => {
        setCorridors(data.corridors);
        setMode(data.mode);
        setUpdatedAt(data.updated_at);
      })
      .catch((e) => setError(e.message));
  }

  async function handleStartSimulation() {
    setSimulating(true);
    try {
      const data = await api.simulate();
      setCorridors(data.corridors);
      setMode(data.mode);
      setUpdatedAt(data.updated_at);
    } catch (e) {
      setError(e.message);
    } finally {
      setSimulating(false);
    }
  }

  if (error) {
    return (
      <div className="app" data-theme={theme}>
        <div className="app-error">
          <p>Can't reach the API at the configured VITE_API_BASE.</p>
          <p className="mono">{error}</p>
        </div>
      </div>
    );
  }

  if (!meta) {
    return (
      <div className="app" data-theme={theme}>
        <div className="app-loading">Loading dashboard…</div>
      </div>
    );
  }

  return (
    <div className="app" data-theme={theme}>
      <Sidebar
        theme={theme}
        setTheme={setTheme}
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
      <MapView
        theme={theme}
        corridors={corridors}
        activeCorridorKey={activeCorridorKey}
        onOpenDetail={setOpenDetailKey}
        destination={meta.destination}
        suppliers={meta.suppliers}
        selectedSource={selectedSource}
        setSelectedSource={setSelectedSource}
      />
      {openDetailKey && (
        <DetailOverlay corridorKey={openDetailKey} onClose={() => setOpenDetailKey(null)} />
      )}
    </div>
  );
}