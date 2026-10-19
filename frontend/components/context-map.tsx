"use client";
import { useEffect } from "react";
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap } from "react-leaflet";
import { mapped, type ContextRecord } from "@/lib/context-types";

function FitRecords({ records, selected }: { records: ContextRecord[]; selected: string }) {
  const map = useMap();
  useEffect(() => {
    const points = records.filter(mapped);
    if (points.length) map.fitBounds(points.map(r => [r.lat, r.lng]), { padding: [25, 25], maxZoom: 11, animate: false });
  }, [records, map]);
  useEffect(() => {
    const record = records.find(r => r.id === selected);
    if (record && mapped(record)) map.setView([record.lat, record.lng], Math.max(map.getZoom(), 9), { animate: false });
  }, [selected, records, map]);
  return null;
}

export default function ContextMap({ records, selected, onSelect, kind }: {
  records: ContextRecord[]; selected: string; onSelect: (id: string) => void; kind: string;
}) {
  return <MapContainer center={[28.3, 85]} zoom={6} className="context-map" scrollWheelZoom={false} aria-label={`${kind} on this result page; equivalent records listed below`}>
    <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    {records.filter(mapped).map(r => <CircleMarker key={r.id} center={[r.lat, r.lng]} radius={r.id === selected ? 9 : 5}
      pathOptions={{ color: kind === "Historical events" ? "#a54b23" : "#087e70", fillOpacity: .7, weight: r.id === selected ? 3 : 1 }}
      eventHandlers={{ click: () => onSelect(r.id) }}><Tooltip>{r.name || r.id}</Tooltip></CircleMarker>)}
    <FitRecords records={records} selected={selected} />
  </MapContainer>;
}
