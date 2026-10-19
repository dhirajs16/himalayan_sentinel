"use client";
import Link from "next/link";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { api, npt } from "@/lib/api";
import { Contributions } from "./lake-monitor";
import type { Lake } from "@/lib/types";
import ObservationCharts, { type Observations } from "./observation-charts";
const LakeMap = dynamic(() => import("./lake-map"), { ssr: false });
export default function LakeProfile({ id }: { id: string }) {
  const [lake, setLake] = useState<Lake | null>(null); const [error, setError] = useState("");
  const [observations, setObservations] = useState<Observations | null>(null);
  const [explanation, setExplanation] = useState<{ summary: string; source: string } | null>(null); const [busy, setBusy] = useState(false);
  useEffect(() => { api<Lake>(`/public/lakes/${encodeURIComponent(id)}`).then(setLake).catch(e => setError(e.message)); }, [id]);
  useEffect(() => { api<Observations>(`/public/lakes/${encodeURIComponent(id)}/observations`).then(setObservations).catch(() => {}); }, [id]);
  async function explain() { setBusy(true); try { setExplanation(await api(`/public/lakes/${encodeURIComponent(id)}/explanation`, { method: "POST" })); } catch (e) { setError((e as Error).message); } finally { setBusy(false); } }
  return <main className="shell"><Link href="/">← Public situation overview</Link>{error && <p role="alert" className="error-message">{error}</p>}{!lake ? <p role="status">{error ? "Lake could not be loaded." : "Loading lake evidence…"}</p> : <>
    <section className="intro"><div><span className="eyebrow accent">Lake profile · {lake.properties.country}</span><h1>{lake.properties.name}</h1><p>{lake.properties.basin} / {lake.properties.sub_basin}</p></div><span className={`risk-pill ${lake.assessment.overall_monitoring_priority.level.toLowerCase()}`}>{lake.assessment.overall_monitoring_priority.level} monitoring priority</span></section>
    <div className="workspace"><div><div className="card map-card"><LakeMap lakes={[lake]} selected={lake.id} onSelect={() => {}} /></div><div className="card panel"><h2>Baseline hazard</h2><dl className="facts"><div><dt>ICIMOD rank</dt><dd>{lake.properties.rank}</dd></div><div><dt>Source area (units unverified)</dt><dd>{lake.properties.area ?? "Unknown"}</dd></div><div><dt>Source elevation (units unverified)</dt><dd>{lake.properties.elevation ?? "Unknown"}</dd></div><div><dt>Inventory publication</dt><dd>{lake.properties.source_date}</dd></div></dl><p>Geometry is the original static inventory polygon. No recent lake-area change, terrain-derived runoff path or downstream population estimate is available.</p></div></div>
    <aside className="card panel"><span className="eyebrow">Automated risk assessment</span><h2>{lake.assessment.overall_monitoring_priority.score} / 100</h2><Contributions assessment={lake.assessment} /><p>Rule version {lake.assessment.version} · Review: {lake.assessment.human_review}</p><p>Mode: <b>{lake.assessment.mode}</b> · Freshness: {lake.assessment.freshness}</p><p>Assessed {npt(lake.assessment.assessed_at)}</p><p>Source time: {lake.assessment.source_observation_time || "Static inventory only"}</p><p className="notice">{lake.assessment.limitations}</p><button className="primary" onClick={explain} disabled={busy}>{busy ? "Preparing draft…" : "AI-assisted explanation"}</button>{explanation && <div className="explain"><b>Draft · {explanation.source}</b><p>{explanation.summary}</p><small>Numerical scores come only from the risk engine. Human review required.</small></div>}</aside></div>
    {observations && <ObservationCharts data={observations} />}
    <section className="card panel"><h2>Exposure and satellite observations</h2><p>Satellite water extent, modelled snowmelt, population and infrastructure exposure are unavailable for this lake. No chart is inferred from missing evidence.</p></section><p className="attribution">{lake.properties.attribution}</p>
  </>}</main>;
}
