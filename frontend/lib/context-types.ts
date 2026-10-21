export type ContextRecord = {
  id: string; name: string; country: string; basin: string; district?: string;
  lat: number | null; lng: number | null; geometry: GeoJSON.GeoJsonObject | null;
  properties: Record<string, unknown>; attribution: string; source_date: string | null;
  year?: string | null; date?: string | null; date_precision?: string; impact?: string | null;
};
export type ContextPage = { items: ContextRecord[]; total: number; offset: number; limit: number };
export type ContextCatalog = {
  sources: { id: string; name: string; status: string; count?: number | null; source_date?: string | null; attribution: string; limitations: string }[];
  districts: { id: string; name: string }[]; limitations: string;
};
export type PopulationContext = {
  status: string; district: string; population: number | null; year: number | null; units: string;
  attribution: string; boundary_attribution?: string; source: string; method: string; valid_cells: number | null; limitations: string;
};
export type ContextWeather = {
  provider: string; mode: string; freshness: string; attribution: string; error?: string | null;
  source_observation_time?: string | null; last_success?: string | null; retrieved_at?: string | null;
  daily?: { time: string[]; precipitation_sum: (number | null)[]; temperature_2m_max: (number | null)[] };
};
export function mapped(record: ContextRecord): record is ContextRecord & { lat: number; lng: number } {
  return typeof record.lat === "number" && Number.isFinite(record.lat) && Math.abs(record.lat) <= 90
    && typeof record.lng === "number" && Number.isFinite(record.lng) && Math.abs(record.lng) <= 180;
}
