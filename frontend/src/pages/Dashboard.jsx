import React, { useEffect, useState, useCallback } from "react";
import Sidebar from "../components/Sidebar.jsx";
import MapView from "../components/MapView.jsx";
import StatsView from "../components/StatsView.jsx";
import DetailOverlay from "../components/DetailOverlay.jsx";
import { api } from "../lib/api";

export default function Dashboard({ theme, setTheme }) {
  const [view, setView] = useState("map"); // "map" | "stats"
  const [meta, setMeta] = useState(null);
  const [corridors, setCorridors] = useState([]);
  const [feederSpurs, setFeederSpurs] = useState([]);
  const [disruptedSuppliers, setDisruptedSuppliers] = useState([]);
  const [mode, setMode] = useState("uninitialized");
  const [updatedAt, setUpdatedAt] = useState(null);
  const [selectedSource, setSelectedSource] = useState(null);
  const [activeCorridorKey, setActiveCorridorKey] = useState(null);
  const [activeRoute, setActiveRoute] = useState(null);
  const [openDetailKey, setOpenDetailKey] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Single helper to batch state updates from corridor API payloads
  const applyCorridorData = useCallback((data) => {
    if (!data) return;
    setCorridors(data.corridors || []);
    setFeederSpurs(data.feeder_spurs || []);
    setDisruptedSuppliers(data.disrupted_suppliers || []);
    setMode(data.mode || "live_monitoring");
    setUpdatedAt(data.updated_at || Date.now());
  }, []);

  // Fetch initial metadata and baseline corridor network
  useEffect(() => {
    let active = true;

    Promise.all([api.meta(), api.corridors()])
      .then(([m, c]) => {
        if (!active) return;
        setMeta(m);
        setSelectedSource(m.suppliers?.[0]?.country ?? null);
        applyCorridorData(c);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });

    return () => {
      active = false;
    };
  }, [applyCorridorData]);

  // Sync selected supplier route whenever the source changes
  const syncActiveRoute = useCallback((source) => {
    if (!source) return;
    api
      .route(source)
      .then((r) => {
        setActiveCorridorKey(r.corridor_key);
        setActiveRoute(r);
      })
      .catch(() => setActiveRoute(null));
  }, []);

  useEffect(() => {
    if (selectedSource && meta) {
      syncActiveRoute(selectedSource);
    }
  }, [selectedSource, meta, syncActiveRoute]);

  // Trigger what-if scenario
  async function handleStartSimulation(customScenario = "") {
    setSimulating(true);
    try {
      const data = await api.simulate(customScenario);
      applyCorridorData(data);
      if (selectedSource) syncActiveRoute(selectedSource);
    } catch (e) {
      setError(e.message);
    } finally {
      setSimulating(false);
    }
  }

  // Clear what-if scenario and return to live baseline
  async function handleResetSimulation() {
    setSimulating(true);
    try {
      const data = api.reset ? await api.reset() : await api.simulate("");
      applyCorridorData(data);
      if (selectedSource) syncActiveRoute(selectedSource);
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
      {/* Floating Toggle Tab */}
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
          onSelectCorridor={setActiveCorridorKey}
          onStartSimulation={handleStartSimulation}
          onResetSimulation={handleResetSimulation}
          simulating={simulating}
          mode={mode}
          updatedAt={updatedAt}
        />
      </div>

      {/* Main Workspace Area */}
      <div className="app-main-view">
        {view === "map" ? (
          <MapView
            theme={theme}
            corridors={corridors}
            feederSpurs={feederSpurs}
            disruptedSuppliers={disruptedSuppliers}
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
        <DetailOverlay
          corridorKey={openDetailKey}
          onClose={() => setOpenDetailKey(null)}
        />
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