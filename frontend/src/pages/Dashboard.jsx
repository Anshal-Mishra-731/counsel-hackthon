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
  const [sidebarOpen, setSidebarOpen] = useState(true);

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

  async function handleStartSimulation(customScenario = "") {
    setSimulating(true);
    try {
      const data = await api.simulate(customScenario);
      setCorridors(data.corridors);
      setMode(data.mode);
      setUpdatedAt(data.updated_at);
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
            Start the backend with <span className="mono">uvicorn src.main:app --reload --port 8000</span>
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
    <div className={`app ${sidebarOpen ? "sidebar-expanded" : "sidebar-collapsed"}`}>
      {/* Floating Toggle Tab - Mounted at Root Layer to evade Leaflet z-index traps */}
      <button
        type="button"
        className="sidebar-floating-toggle"
        onClick={() => setSidebarOpen((prev) => !prev)}
        title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 10 10"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            transform: sidebarOpen ? "rotate(0deg)" : "rotate(180deg)",
            transition: "transform 0.25s ease",
          }}
        >
          <path d="M6.5 2L3.5 5L6.5 8" />
        </svg>
      </button>

      {/* Collapsible Sidebar Wrapper */}
      <div className="app-sidebar-wrap">
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
      </div>

      {/* Main View Area */}
      <div className="app-main-view">
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
      </div>

      {openDetailKey && (
        <DetailOverlay corridorKey={openDetailKey} onClose={() => setOpenDetailKey(null)} />
      )}

      <style>{`
        .app {
          display: flex;
          height: 100vh;
          width: 100vw;
          overflow: hidden;
          position: relative;
          background: #04080e;
        }

        /* Dedicated Sidebar Viewport Track */
        .app-sidebar-wrap {
          height: 100%;
          position: relative;
          z-index: 1000;
          overflow: hidden;
          transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1),
                      min-width 0.3s cubic-bezier(0.16, 1, 0.3, 1),
                      opacity 0.25s ease;
        }

        .sidebar-expanded .app-sidebar-wrap {
          width: 340px;
          min-width: 340px;
          opacity: 1;
        }

        .sidebar-collapsed .app-sidebar-wrap {
          width: 0 !important;
          min-width: 0 !important;
          opacity: 0;
          pointer-events: none;
        }

        /* Persistent Floating Toggle Tab */
        .sidebar-floating-toggle {
          position: fixed;
          top: 50%;
          transform: translateY(-50%);
          z-index: 9999;
          width: 20px;
          height: 52px;
          padding: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #0b1522;
          border: 1px solid #1a2a3c;
          border-left: none;
          border-radius: 0 8px 8px 0;
          color: #8da4be;
          cursor: pointer;
          box-shadow: 4px 0 16px rgba(0, 0, 0, 0.6);
          transition: left 0.3s cubic-bezier(0.16, 1, 0.3, 1),
                      background 0.2s ease,
                      color 0.2s ease,
                      border-color 0.2s ease;
        }

        .sidebar-expanded .sidebar-floating-toggle {
          left: 340px;
        }

        .sidebar-collapsed .sidebar-floating-toggle {
          left: 0px;
        }

        .sidebar-floating-toggle:hover {
          color: #2dd4bf;
          background: #0e1e30;
          border-color: rgba(45, 212, 191, 0.5);
        }

        /* Main Workspace View */
        .app-main-view {
          flex: 1;
          height: 100%;
          position: relative;
          overflow: hidden;
          min-width: 0;
        }
      `}</style>
    </div>
  );
}