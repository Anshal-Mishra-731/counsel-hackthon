import React, { useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer, Polyline, Marker, Tooltip } from "react-leaflet";
import L from "leaflet";
import { RISK_COLORS } from "../lib/api";

const TILE = {
  dark: {
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
  light: {
    url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
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
  activeRoute,
  onOpenDetail,
  destination,
  suppliers,
  selectedSource,
  setSelectedSource,
  showAllRoutes = false,   // default OFF: sirf selected/simulated route dikhega
  hasSimulated = false,    // true jab tak current source pe simulate ho chuka ho
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

  // Active route ke liye final waypoints nikalo — agar selected source ka
  // apna port coordinate backend ke pehle waypoint se kaafi door hai, to
  // usko shuru me jod do taaki route uss country ke asli port se nikalta dikhe.
  let finalActiveWaypoints = null;
  if (activeRoute?.waypoints?.length > 1) {
    const sourceSupplier = suppliers.find((s) => s.country === selectedSource);
    const backendWaypoints = activeRoute.waypoints;
    finalActiveWaypoints = backendWaypoints;
    if (sourceSupplier) {
      const sourcePoint = [sourceSupplier.lat, sourceSupplier.lng];
      const [firstLat, firstLng] = backendWaypoints[0];
      const dist = Math.hypot(firstLat - sourcePoint[0], firstLng - sourcePoint[1]);
      if (dist > 0.5) {
        finalActiveWaypoints = [sourcePoint, ...backendWaypoints];
      }
    }
  }

  const routeKey = activeRoute
    ? `${activeRoute.corridor_key}-${selectedSource}-${hasSimulated ? "sim" : "sel"}`
    : "none";

  return (
    <div className="map-area" ref={wrapperRef}>
      <div className="map-topbar">
        <div className="map-badge">
          {selectedSource ? `${selectedSource} → ${destination.name}` : "Select a source"}
          {hasSimulated && <span className="map-badge-sim"> · simulated route locked ⚡</span>}
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
        <TileLayer key={theme} url={tile.url} attribution={tile.attribution} subdomains={["a", "b", "c", "d"]} />

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

        {/* 1) BASELINE — sirf tab dikhega jab showAllRoutes = true */}
        {showAllRoutes &&
          corridors.map((c) => (
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

        {showAllRoutes &&
          corridors.map((c) => (
            <Marker
              key={`buoy-${c.key}`}
              position={midpoint(c.waypoints)}
              icon={buoyIcon(RISK_COLORS[c.risk_bucket] || "#8ba3ba", c.key === activeCorridorKey)}
              eventHandlers={{ click: () => onOpenDetail(c.key) }}
            >
              <Tooltip direction="top">{c.name} · risk {c.risk_score}/100 · click for details</Tooltip>
            </Marker>
          ))}

        {/* 2) ACTIVE ROUTE — simulate se pehle normal risk-colored line,
               simulate ke baad glow-halo + dark-core (2 layers) taaki dark
               basemap ke against bhi line hamesha clearly visible rahe */}
        {finalActiveWaypoints && !hasSimulated && (
          <Polyline
            key={`active-${routeKey}`}
            positions={finalActiveWaypoints}
            pathOptions={{
              color: RISK_COLORS[activeRoute.risk_bucket] || "#2dd4bf",
              weight: 5,
              opacity: 0.95,
              dashArray: activeRoute.traffic_halted ? "2 10" : null,
            }}
          />
        )}

        {finalActiveWaypoints && hasSimulated && (
          <React.Fragment key={`active-group-${routeKey}`}>
            <Polyline
              key={`glow-${routeKey}`}
              positions={finalActiveWaypoints}
              pathOptions={{
                color: "#37c9e0",
                weight: 12,
                opacity: 0.45,
                lineCap: "round",
                lineJoin: "round",
                className: "simulated-route-glow",
              }}
            />
            <Polyline
              key={`core-${routeKey}`}
              positions={finalActiveWaypoints}
              pathOptions={{
                color: "#04070c",
                weight: 5,
                opacity: 1,
                dashArray: "16 10",
                lineCap: "round",
                lineJoin: "round",
                className: "simulated-route-core",
              }}
            />
          </React.Fragment>
        )}

        {/* start/end pulse marker on the simulated route so it really pops */}
        {hasSimulated && finalActiveWaypoints && (
          <Marker
            position={finalActiveWaypoints[finalActiveWaypoints.length - 1]}
            icon={L.divIcon({
              className: "",
              html: `<div class="sim-pulse-marker"></div>`,
              iconSize: [26, 26],
              iconAnchor: [13, 13],
            })}
          />
        )}
      </MapContainer>

      <style>{`
        /* Glow halo — static bright cyan blur, taaki dark line map ke
           background me kabhi merge na ho, hamesha ek halo se surrounded ho */
        .simulated-route-glow {
          filter: blur(3px);
          animation: sim-glow-breathe 2.2s ease-in-out infinite;
        }
        @keyframes sim-glow-breathe {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 0.65; }
        }

        /* Dark core line — marching-ants animation, sirf stroke-dashoffset
           animate karta hai (widely supported, reliable render) */
        .simulated-route-core {
          animation: sim-dash-flow 1s linear infinite;
        }
        @keyframes sim-dash-flow {
          to { stroke-dashoffset: -52; }
        }

        .sim-pulse-marker {
          width: 16px; height: 16px; border-radius: 50%;
          background: #04070c;
          box-shadow: 0 0 0 0 rgba(56,201,224,0.7);
          animation: sim-pulse-ring 1.6s ease-out infinite;
        }
        @keyframes sim-pulse-ring {
          0% { box-shadow: 0 0 0 0 rgba(56,201,224,0.6); }
          70% { box-shadow: 0 0 0 16px rgba(56,201,224,0); }
          100% { box-shadow: 0 0 0 0 rgba(56,201,224,0); }
        }
        .map-badge-sim { color: #37c9e0; font-weight: 600; }
      `}</style>
    </div>
  );
}