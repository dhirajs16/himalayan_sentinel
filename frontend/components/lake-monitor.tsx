"use client";
import Link from "next/link";
import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import { api, npt } from "@/lib/api";
import { translations } from "@/lib/i18n";
import type { Assessment, Lake, PublicAlert } from "@/lib/types";
const LakeMap = dynamic(() => import("./lake-map"), { ssr: false, loading: () => <div className="map loading" role="status">Loading lake polygons…</div> });

export function Contributions({ assessment }: { assessment: Assessment }) {
  return <div className="contributions" aria-label="Monitoring score contributions">
    {assessment.components.map(c => <div className="contribution" key={c.key}><div><span>{c.key.replaceAll("_", " ")}</span><b>{c.status === "missing" ? "Unknown" : `${c.contribution.toFixed(1)} / ${c.weight}`}</b></div><meter min={0} max={c.weight} value={c.contribution} aria-label={`${c.key}: ${c.status === "missing" ? "unknown" : c.contribution + " points"}`} /></div>)}
    <p className="notice">Completeness {assessment.completeness}% · evidence confidence {assessment.evidence_confidence}% (prototype indicator, not statistical probability). Missing data does not mean low hazard.</p>
  </div>;
}

export function PublicAlerts({ language = "en" }: { language?: "en" | "ne" }) {
  const [alerts, setAlerts] = useState<PublicAlert[]>([]);
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);
  useEffect(() => {
    let active = true;
    const refresh = () => api<{ items: PublicAlert[] }>("/public/alerts").then(r => { if (active) { setAlerts(r.items); setError(""); setReady(true); } }).catch(() => { if (active) setError("Alert service unavailable. Check official local channels."); });
    refresh(); const timer = setInterval(refresh, 15000);
    return () => { active = false; clearInterval(timer); };
  }, []);
  const t = translations[language];
  return <section className="card panel" aria-labelledby="public-alerts-title"><div className="section-title"><div><span className="eyebrow">Human reviewed</span><h2 id="public-alerts-title">{t.alerts}</h2></div><span className="muted">Refreshes every 15s</span></div>
    {error ? <p role="alert" className="error-message">{error}</p> : !ready ? <p role="status">Loading alerts…</p> : !alerts.length ? <p className="empty">{t.noAlerts}. This does not establish safe conditions. {t.follow}.</p> :
      <ol className="alert-timeline">{alerts.map(a => <li key={a.id}><div className="section-title"><h3>{a.title}</h3><span className={`risk-pill ${a.severity.toLowerCase()}`}>{a.severity}</span></div>{a.is_demo && <strong className="demo-tag">DEMO · local publication only</strong>}<p>{a.description}</p><p><b>{t.safety}:</b> {a.safety_instructions}</p><details><summary>Evidence and validity</summary><p>{a.evidence_summary}</p><p>{a.region} · Published {npt(a.published_at)}</p><p>Effective {npt(a.effective_at)} · Expires {npt(a.expires_at)}</p></details></li>)}</ol>}
  </section>;
}

export default function LakeMonitor() {
  const [lakes, setLakes] = useState<Lake[]>([]);
  const [q, setQ] = useState(""); const [basin, setBasin] = useState(""); const [country, setCountry] = useState("");
  const [selected, setSelected] = useState(""); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  const load = () => { setLoading(true); api<{ items: Lake[] }>("/public/lakes").then(r => { setLakes(r.items); setSelected(r.items[0]?.id || ""); setError(""); }).catch((e: Error) => setError(e.message)).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, []);
  const filtered = useMemo(() => lakes.filter(l => JSON.stringify(l.properties).toLowerCase().includes(q.toLowerCase()) && (!basin || l.properties.basin === basin) && (!country || l.properties.country === country)), [lakes, q, basin, country]);
  return <section id="lakes" className="lake-monitor"><div className="section-title"><div><span className="eyebrow accent">ICIMOD · static hazard inventory</span><h2>Glacial lake monitoring</h2><p className="muted">Original lake polygons and baseline ranks across Nepal, China and India. Dynamic indicators are labelled separately.</p></div><Link className="secondary" href="/operations">Staff workspace →</Link></div>
    <div className="filters"><label>Search lake, country or sub-basin<input value={q} onChange={e => setQ(e.target.value)} placeholder="Lake identifier or basin…" /></label><label>Basin<select value={basin} onChange={e => setBasin(e.target.value)}><option value="">All basins</option>{Array.from(new Set(lakes.map(l => l.properties.basin))).map(b => <option key={b}>{b}</option>)}</select></label><label>Country<select value={country} onChange={e => setCountry(e.target.value)}><option value="">All countries</option>{Array.from(new Set(lakes.map(l => l.properties.country))).map(b => <option key={b}>{b}</option>)}</select></label></div>
    {error && <p role="alert" className="error-message">Lake API unavailable: {error} <button onClick={load}>Retry</button></p>}
    {loading ? <div className="skeleton" role="status">Loading lake inventory…</div> : !lakes.length ? <p className="notice">No lake inventory imported. Run the documented preprocessing and import commands with your licensed local data.</p> : <div className="workspace"><div className="card map-card"><LakeMap lakes={filtered} selected={selected} onSelect={setSelected} /></div><div className="card panel lake-list"><h3>Monitoring priority · {filtered.length} lakes</h3>{!filtered.length && <p>No matching lakes.</p>}{filtered.map(l => <div key={l.id} className={`lake-row ${selected === l.id ? "selected" : ""}`}><button onClick={() => setSelected(l.id)}><b>{l.properties.name}</b><span>{l.properties.country} · {l.properties.sub_basin}</span><span>Baseline Rank {l.properties.rank} · {l.assessment.mode}</span></button><div><span className={`risk-pill ${l.assessment.overall_monitoring_priority.level.toLowerCase()}`}>{l.assessment.overall_monitoring_priority.level} · {l.assessment.overall_monitoring_priority.score}</span><Link href={`/lakes/${encodeURIComponent(l.id)}`}>View evidence →</Link></div></div>)}</div></div>}
    <p className="attribution">ICIMOD (2020), Potentially dangerous glacial lakes in the Koshi, Gandaki, and Karnali river basins of Nepal, the Tibet Autonomous Region of China, and India. <a href="https://doi.org/10.26066/RDS.1971950">Dataset and attribution</a>. Static inventory; not a current prediction feed.</p>
  </section>;
}
