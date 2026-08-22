import React, { useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer, Polyline, Marker, Tooltip } from "react-leaflet";
import L from "leaflet";
import { RISK_COLORS } from "../lib/api";

const TILE = {
  dark: {
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
  light: {
    url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
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
  theme, corridors, activeCorridorKey, onOpenDetail,
  destination, suppliers, selectedSource, setSelectedSource,
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
        <TileLayer
          key={theme}
          url={tile.url}
          attribution={tile.attribution}
          subdomains={["a", "b", "c", "d"]}
        />

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

        {corridors.map((c) => {
          const color = RISK_COLORS[c.risk_bucket] || "#8ba3ba";
          const isActive = c.key === activeCorridorKey;
          return (
            <React.Fragment key={c.key}>
              <Polyline
                positions={c.waypoints}
                pathOptions={{
                  color,
                  weight: isActive ? 5 : 3,
                  opacity: isActive ? 0.95 : 0.55,
                  dashArray: c.traffic_halted ? "2 10" : null,
                }}
                eventHandlers={{ click: () => onOpenDetail(c.key) }}
              />
              {/* floating "buoy" button on each route — click for the full detail overlay */}
              <Marker
                position={midpoint(c.waypoints)}
                icon={buoyIcon(color, isActive)}
                eventHandlers={{ click: () => onOpenDetail(c.key) }}
              >
                <Tooltip direction="top">{c.name} · risk {c.risk_score}/100 · click for details</Tooltip>
              </Marker>
            </React.Fragment>
          );
        })}
      </MapContainer>
    </div>
  );
}
