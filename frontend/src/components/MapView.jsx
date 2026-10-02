import React, { useEffect, useRef, useState } from "react";
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
  return waypoints[Math.floor(waypoints.length / 2)];
}

function buoyIcon(color, isActive) {
  return L.divIcon({
    className: "",
    html: `<div class="route-buoy ${isActive ? "route-buoy--active" : ""}" style="--buoy-color:${color}">⛴</div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
}

function portIcon(color, big) {
  const size = big ? 16 : 11;
  return L.divIcon({
    className: "",
    html: `<div class="port-dot" style="width:${size}px;height:${size}px;background:${color};box-shadow:0 0 0 4px ${color}33"></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

export default function MapView({
  theme,
  corridors,
  activeCorridorKey,
  activeRoute, // NEW — { waypoints, corridor_key, risk_bucket, traffic_halted, ... } from api.route(source)
  onOpenDetail,
  destination,
  suppliers,
  selectedSource,
  setSelectedSource,
}) {
  const wrapperRef = useRef(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const tile = TILE[theme] || TILE.dark;

  useEffect(() => {
    const onChange = () => setIsFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) wrapperRef.current?.requestFullscreen?.();
    else document.exitFullscreen?.();
  };

  return (
    <div className="map-area" ref={wrapperRef}>
      <div className="map-topbar">
        <div className="map-badge">
          {selectedSource ? `${selectedSource} → ${destination.name}` : "Select a source"}
        </div>
        <button
          className="icon-btn"
          title={isFullscreen ? "Exit full screen" : "Full screen"}
          onClick={toggleFullscreen}
        >
          {isFullscreen ? "⤡ Exit" : "⤢ Fullscreen"}
        </button>
      </div>

      <MapContainer center={[15, 55]} zoom={3} minZoom={2} worldCopyJump>
        <TileLayer key={theme} url={tile.url} attribution={tile.attribution} />

        <Marker position={[destination.lat, destination.lng]} icon={portIcon("#2dd4bf", true)}>
          <Tooltip direction="top">📍 {destination.name} · {destination.port}</Tooltip>
        </Marker>

        {suppliers.map((s) => (
          <Marker
            key={s.country}
            position={[s.lat, s.lng]}
            icon={portIcon(s.country === selectedSource ? "#2dd4bf" : "#8ba3ba", s.country === selectedSource)}
            eventHandlers={{ click: () => setSelectedSource(s.country) }}
          >
            <Tooltip direction="top">{s.country} · {s.port}</Tooltip>
          </Marker>
        ))}

        {/* 1) BASELINE — every corridor, always drawn LIGHT so you can see all
               possible routes at once, regardless of what's selected */}
        {corridors.map((c) => (
          <Polyline
            key={`base-${c.key}`}
            positions={c.waypoints}
            pathOptions={{
              color: RISK_COLORS[c.risk_bucket] || "#8ba3ba",
              weight: 2,
              opacity: c.key === activeRoute?.corridor_key ? 0.18 : 0.4,
              dashArray: c.traffic_halted ? "2 10" : null,
            }}
            eventHandlers={{ click: () => onOpenDetail(c.key) }}
          />
        ))}

        {/* 2) floating "buoy" per corridor — always clickable for full detail,
               dims/brightens to show which one matches the current selection */}
        {corridors.map((c) => (
          <Marker
            key={`buoy-${c.key}`}
            position={midpoint(c.waypoints)}
            icon={buoyIcon(RISK_COLORS[c.risk_bucket] || "#8ba3ba", c.key === activeCorridorKey)}
            eventHandlers={{ click: () => onOpenDetail(c.key) }}
          >
            <Tooltip direction="top">{c.name} · risk {c.risk_score}/100 · click for details</Tooltip>
          </Marker>
        ))}

        {/* 3) ACTIVE ROUTE — the ONE bold/dark line: selected source's own port,
               through its real spur, to the corridor chokepoint, into India.
               This is what was missing before — without it, every source just
               looked like it was reusing the same generic corridor trunk. */}
        {activeRoute?.waypoints?.length > 1 && (
          <Polyline
            key={`active-${activeRoute.corridor_key}-${selectedSource}`}
            positions={activeRoute.waypoints}
            pathOptions={{
              color: RISK_COLORS[activeRoute.risk_bucket] || "#2dd4bf",
              weight: 5,
              opacity: 0.95,
              dashArray: activeRoute.traffic_halted ? "2 10" : null,
            }}
          />
        )}
      </MapContainer>
    </div>
  );
}
