export type RiskLevel = "Low" | "Moderate" | "High" | "Critical";
export type Assessment = {
  version: string; assessed_at: string; mode: string; freshness: string;
  source_observation_time: string | null;
  baseline_hazard: { rank: string | null; score: number | null };
  overall_monitoring_priority: { score: number; level: RiskLevel };
  components: { key: string; value: number | null; weight: number; contribution: number; status: string }[];
  evidence_confidence: number; completeness: number; limitations: string; human_review: string;
};
export type Lake = {
  id: string; source_id: string; lat: number; lng: number;
  geometry: GeoJSON.Geometry;
  properties: { name: string; rank: string; country: string; basin: string; sub_basin?: string; area?: number; elevation?: number; attribution: string; source_date: string; [key: string]: unknown };
  assessment: Assessment;
};
export type PublicAlert = { id: string; title: string; region: string; severity: RiskLevel; status: string; description: string; safety_instructions: string; evidence_summary: string; effective_at: string; expires_at: string; published_at: string; is_demo: boolean };
export type Region = {
  id: string;
  name: string;
  province: string;
  basin: string;
  lat: number;
  lng: number;
  rainfall_mm: number;
  river_status: string;
  glacial_risk: string;
  reports: number;
  population_exposed: number;
  trend: number[];
  rainfall_trend: number[];
  risk: {
    score: number;
    level: RiskLevel;
    factors: Record<string, number>;
    weights: Record<string, number>;
  };
};
