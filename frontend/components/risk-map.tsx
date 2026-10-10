"use client";
import { CircleMarker, MapContainer, TileLayer, Tooltip } from "react-leaflet";
import type { Region, RiskLevel } from "@/lib/types";
const colors:Record<RiskLevel,string>={Low:"#28a66b",Moderate:"#eab93d",High:"#e77b32",Critical:"#dc4b4b"};
export default function RiskMap({regions,selected,onSelect}:{regions:Region[];selected:string;onSelect:(r:Region)=>void}){
 return <MapContainer center={[28.2,84.9]} zoom={7} scrollWheelZoom className="map"><TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>{regions.map(r=><CircleMarker key={r.id} center={[r.lat,r.lng]} radius={selected===r.id?18:12} pathOptions={{color:"#fff",weight:3,fillColor:colors[r.risk.level],fillOpacity:.92}} eventHandlers={{click:()=>onSelect(r)}}><Tooltip direction="top"><strong>{r.name}</strong><br/>{r.risk.level} · {r.risk.score}/100</Tooltip></CircleMarker>)}</MapContainer>
}
