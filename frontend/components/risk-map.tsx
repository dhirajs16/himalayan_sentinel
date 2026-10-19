"use client";
import { CircleMarker, MapContainer, TileLayer, Tooltip } from "react-leaflet";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PublicAlert } from "@/lib/types";
import type { Region, RiskLevel } from "@/lib/types";
const colors: Record<RiskLevel, string> = {
  Low: "#28a66b",
  Moderate: "#eab93d",
  High: "#e77b32",
  Critical: "#dc4b4b",
};
export default function RiskMap({
  regions,
  selected,
  onSelect,
}: {
  regions: Region[];
  selected: string;
  onSelect: (r: Region) => void;
}) {
  const [alerts, setAlerts] = useState<PublicAlert[]>([]);
  useEffect(() => {
    const refresh = () => api<{ items: PublicAlert[] }>("/public/alerts").then(r => setAlerts(r.items)).catch(() => setAlerts([]));
    refresh(); const timer = setInterval(refresh, 15000); return () => clearInterval(timer);
  }, []);
  return (
    <MapContainer
      center={[28.2, 84.9]}
      zoom={7}
      scrollWheelZoom
      className="map"
    >
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {regions.map((r) => (
        <CircleMarker
          key={r.id}
          center={[r.lat, r.lng]}
          radius={selected === r.id ? 18 : 12}
          pathOptions={{
            color: "#fff",
            weight: 3,
            fillColor: colors[r.risk.level],
            fillOpacity: 0.92,
          }}
          eventHandlers={{ click: () => onSelect(r) }}
        >
          <Tooltip direction="top">
            <strong>{r.name}</strong>
            <br />
            {r.risk.level} · {r.risk.score}/100
          </Tooltip>
        </CircleMarker>
      ))}
      {alerts.map(alert => {
        const region = regions.find(r => r.id === alert.region);
        return region ? <CircleMarker key={alert.id} center={[region.lat, region.lng]} radius={24} pathOptions={{ color: "#842c3b", weight: 3, dashArray: "5 4", fillOpacity: 0 }}><Tooltip><b>{alert.is_demo ? "DEMO · " : ""}{alert.title}</b><br />Published notice · approximate district centre<br />{alert.severity} · {alert.status}</Tooltip></CircleMarker> : null;
      })}
    </MapContainer>
  );
}
