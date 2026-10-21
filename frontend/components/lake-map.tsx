"use client";
import { useEffect, useState } from "react";
import { CircleMarker, GeoJSON, MapContainer, TileLayer, Tooltip, useMap } from "react-leaflet";
import { api } from "@/lib/api";
import type { Lake, RiskLevel } from "@/lib/types";
const colors: Record<RiskLevel, string> = { Low: "#23724d", Moderate: "#9b7608", High: "#be5314", Critical: "#c23137" };
function Focus({ lake }: { lake?: Lake }) {
  const map = useMap();
  useEffect(() => { if (lake) map.flyTo([lake.lat, lake.lng], Math.max(map.getZoom(), 9), { animate: !window.matchMedia("(prefers-reduced-motion: reduce)").matches }); }, [lake, map]);
  return null;
}
export default function LakeMap({ lakes, selected, onSelect }: { lakes: Lake[]; selected: string; onSelect: (id: string) => void }) {
  const [boundaries, setBoundaries] = useState<GeoJSON.GeoJsonObject | null>(null);
  useEffect(() => { api<GeoJSON.GeoJsonObject>("/public/boundaries/provinces").then(setBoundaries).catch(() => {}); }, []);
  return <MapContainer center={[28.5, 85]} zoom={7} className="map" scrollWheelZoom={false} aria-label="Glacial lake polygon map">
    <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    {boundaries && <GeoJSON data={boundaries} attribution='<a href="https://localboundries.oknp.org/">Boundaries: Open Knowledge Nepal</a> (<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>)' style={{ color: "#426f69", weight: 1, fillOpacity: 0.02 }} />}
    {lakes.map(l => <GeoJSON key={l.id + (selected === l.id)} data={l.geometry} style={{ color: colors[l.assessment.overall_monitoring_priority.level], weight: selected === l.id ? 4 : 2, fillOpacity: .5 }} eventHandlers={{ click: () => onSelect(l.id) }} />)}
    {lakes.map(l => <CircleMarker key={l.id} center={[l.lat, l.lng]} radius={selected === l.id ? 9 : 5} pathOptions={{ color: colors[l.assessment.overall_monitoring_priority.level], fillOpacity: .8 }} eventHandlers={{ click: () => onSelect(l.id) }}><Tooltip><b>{l.id}</b><br />Baseline Rank {l.properties.rank}<br />{l.assessment.overall_monitoring_priority.level} monitoring priority</Tooltip></CircleMarker>)}
    <Focus lake={lakes.find(l => l.id === selected)} />
  </MapContainer>;
}
