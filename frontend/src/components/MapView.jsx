import React from "react";
import { MapContainer, TileLayer, Polyline, Marker, Tooltip } from "react-leaflet";
import L from "leaflet";
import { RISK_COLORS } from "../lib/api";

const TILE = {
  dark: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    attribution: '&copy; <a href="https://www.esri.com/">Esri</a> &copy; OpenStreetMap contributors',
  },
  light: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    attribution: '&copy; <a href="https://www.esri.com/">Esri</a> &copy; OpenStreetMap contributors',
  },
};

function midpoint(waypoints) {
  if (!waypoints || waypoints.length === 0) return [20, 60];
  return waypoints[Math.floor(waypoints.length / 2)];
}

function buoyIcon(color, isActive) {
  return L.divIcon({
    className: "",
    html: `
      <div class="route-buoy ${isActive ? "route-buoy--active" : ""}" style="--buoy-color:${color}">
        <span>⚓</span>
      </div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function portIcon(color, isSelected, isIndiaHub = false) {
  const size = isIndiaHub ? 14 : isSelected ? 12 : 8;
  const borderCol = isIndiaHub ? "#38bdf8" : isSelected ? "#2dd4bf" : "#ffffff";
  const glow = isIndiaHub
    ? "0 0 10px rgba(56, 189, 248, 0.8)"
    : isSelected
    ? "0 0 12px rgba(45, 212, 191, 0.9)"
    : "0 0 4px rgba(0, 0, 0, 0.6)";

  return L.divIcon({
    className: "",
    html: `
      <div class="port-marker-dot" style="
        width:${size}px;
        height:${size}px;
        background:${color};
        border: 2px solid ${borderCol};
        border-radius: 50%;
        box-shadow:${glow};
        cursor: pointer;
        transition: transform 0.15s ease;
      "></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

export default function MapView({
  theme,
  corridors = [],
  activeCorridorKey,
  activeRoute,
  onOpenDetail,
  destination,
  suppliers = [],
  selectedSource,
  setSelectedSource,
}) {
  const tile = TILE[theme] || TILE.dark;
  const domesticHubs = destination?.hubs || [
    { name: destination?.name || "India Hub", port: destination?.port || "Mundra", lat: destination?.lat || 22.47, lng: destination?.lng || 69.84 }
  ];

  return (
    <div className="map-area">
      <MapContainer
        center={[15, 60]}
        zoom={3}
        minZoom={2}
        maxZoom={10}
        worldCopyJump
        style={{ height: "100%", width: "100%", background: "#04080e" }}
      >
        <TileLayer key={theme} url={tile.url} attribution={tile.attribution} />

        {/* 1) Indian Domestic Destination Refinery Hubs */}
        {domesticHubs.map((hub, idx) => (
          <Marker
            key={`hub-${idx}`}
            position={[hub.lat, hub.lng]}
            icon={portIcon("#38bdf8", false, true)}
          >
            <Tooltip direction="top" offset={[0, -8]}>
              <div style={{ fontSize: "11px", fontWeight: 700 }}>🇮🇳 {hub.name}</div>
              <div style={{ fontSize: "10px", color: "#94a3b8" }}>{hub.port}</div>
              {hub.capacity_bpd && (
                <div style={{ fontSize: "10px", color: "#38bdf8", fontFamily: "monospace" }}>
                  {(hub.capacity_bpd / 1000).toFixed(0)}k bpd refining capacity
                </div>
              )}
            </Tooltip>
          </Marker>
        ))}

        {/* 2) Global Crude Supplier Ports */}
        {suppliers.map((s) => {
          const isSelected = s.country === selectedSource;
          return (
            <Marker
              key={s.country}
              position={[s.lat, s.lng]}
              icon={portIcon(isSelected ? "#2dd4bf" : "#f59e0b", isSelected, false)}
              eventHandlers={{ click: () => setSelectedSource(s.country) }}
            >
              <Tooltip direction="top" offset={[0, -6]}>
                <div style={{ fontSize: "11.5px", fontWeight: 700, color: "#f8fafc" }}>
                  {s.country}
                </div>
                <div style={{ fontSize: "10px", color: "#cbd5e1" }}>{s.port}</div>
                {s.volume_bpd && (
                  <div style={{ fontSize: "10px", color: "#2dd4bf", fontFamily: "monospace", marginTop: "2px" }}>
                    Normal flow: {(s.volume_bpd / 1000).toFixed(0)}k bpd
                  </div>
                )}
                <div style={{ fontSize: "9px", color: "#94a3b8", textTransform: "uppercase", marginTop: "2px" }}>
                  via {s.corridor?.replace(/_/g, " ")}
                </div>
              </Tooltip>
            </Marker>
          );
        })}

        {/* 3) Baseline Network Corridors */}
        {corridors.map((c) => (
          <Polyline
            key={`base-${c.key}`}
            positions={c.waypoints}
            pathOptions={{
              color: RISK_COLORS[c.risk_bucket] || "#64748b",
              weight: 2.2,
              opacity: c.key === activeRoute?.corridor_key ? 0.2 : 0.45,
              lineCap: "round",
              lineJoin: "round",
              dashArray: c.traffic_halted ? "4 8" : null,
            }}
            eventHandlers={{ click: () => onOpenDetail(c.key) }}
          />
        ))}

        {/* 4) Interactive Corridor Chokepoint Buoys */}
        {corridors.map((c) => (
          <Marker
            key={`buoy-${c.key}`}
            position={midpoint(c.waypoints)}
            icon={buoyIcon(RISK_COLORS[c.risk_bucket] || "#8ba3ba", c.key === activeCorridorKey)}
            eventHandlers={{ click: () => onOpenDetail(c.key) }}
          >
            <Tooltip direction="top" offset={[0, -10]}>
              <div style={{ fontSize: "11px", fontWeight: 700 }}>{c.name}</div>
              <div style={{ fontSize: "10px", color: RISK_COLORS[c.risk_bucket] }}>
                Threat: {c.risk_score}/100 {c.traffic_halted ? "· (HALTED)" : ""}
              </div>
              <div style={{ fontSize: "9px", color: "#94a3b8" }}>Click to open operational brief</div>
            </Tooltip>
          </Marker>
        ))}

        {/* 5) Active Selection Route with Dual-Layer Glow */}
        {activeRoute?.waypoints?.length > 1 && (
          <>
            {/* Ambient Halos */}
            <Polyline
              key={`glow-${activeRoute.corridor_key}-${selectedSource}`}
              positions={activeRoute.waypoints}
              pathOptions={{
                color: RISK_COLORS[activeRoute.risk_bucket] || "#2dd4bf",
                weight: 12,
                opacity: 0.18,
                lineCap: "round",
                lineJoin: "round",
              }}
            />
            {/* Core Sharp Vector */}
            <Polyline
              key={`active-${activeRoute.corridor_key}-${selectedSource}`}
              positions={activeRoute.waypoints}
              pathOptions={{
                color: RISK_COLORS[activeRoute.risk_bucket] || "#2dd4bf",
                weight: 3.5,
                opacity: 0.95,
                lineCap: "round",
                lineJoin: "round",
                dashArray: activeRoute.traffic_halted ? "6 8" : null,
              }}
            />
          </>
        )}
      </MapContainer>

      <style>{`
        .map-area {
          position: relative;
          width: 100%;
          height: 100%;
          background: #04080e;
        }
        .route-buoy {
          width: 26px;
          height: 26px;
          border-radius: 50%;
          background: #0b1522;
          border: 1.5px solid var(--buoy-color, #2dd4bf);
          box-shadow: 0 0 10px rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 13px;
          cursor: pointer;
          transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s;
        }
        .route-buoy:hover {
          transform: scale(1.3);
          box-shadow: 0 0 14px var(--buoy-color, #2dd4bf);
        }
        .route-buoy--active {
          box-shadow: 0 0 16px var(--buoy-color, #2dd4bf);
          border-width: 2px;
          transform: scale(1.15);
        }
        .port-marker-dot:hover {
          transform: scale(1.6);
        }
        /* Custom Leaflet Tooltip Overrides */
        .leaflet-tooltip {
          background: rgba(11, 21, 34, 0.92) !important;
          border: 1px solid #1e293b !important;
          border-radius: 6px !important;
          padding: 6px 10px !important;
          color: #f1f5f9 !important;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6) !important;
          backdrop-filter: blur(6px);
        }
        .leaflet-tooltip-top:before {
          border-top-color: #1e293b !important;
        }
      `}</style>
    </div>
  );
}