"use client";
import dynamic from "next/dynamic";
import { useEffect, useId, useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import { mapped, type ContextCatalog, type ContextPage, type ContextWeather, type PopulationContext } from "@/lib/context-types";
import "./evidence-explorer.css";

const ContextMap = dynamic(() => import("./context-map"), { ssr: false, loading: () => <p role="status">Loading context map…</p> });
type Remote<T> = { data?: T; loading: boolean; error?: string };
function useContextResource<T>(path: string | null): Remote<T> {
  const [state, setState] = useState<Remote<T>>({ loading: !!path });
  useEffect(() => {
    let active = true;
    if (!path) { setState({ loading: false }); return; }
    setState({ loading: true });
    api<T>(path).then(data => { if (active) setState({ data, loading: false }); })
      .catch(error => { if (active) setState({ loading: false, error: error.message || "Data unavailable" }); });
    return () => { active = false; };
  }, [path]);
  return state;
}
function time(value?: string | null) {
  if (!value) return "Unknown";
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  const date = new Date(value);
  return Number.isFinite(date.getTime()) ? new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Kathmandu" }).format(date) + " NPT" : value;
}
function Value({ value }: { value: unknown }) {
  const text = value === null || value === undefined ? "Unknown" : typeof value === "object" ? JSON.stringify(value) : String(value);
  try {
    const url = new URL(text);
    if (url.protocol === "https:" || url.protocol === "http:") return <a href={url.href} target="_blank" rel="noopener noreferrer">{text}</a>;
  } catch { /* Non-URL attributes remain escaped React text. */ }
  return <>{text}</>;
}
function ResourceState({ loading, error }: { loading: boolean; error?: string }) {
  return loading ? <p role="status">Loading evidence…</p> : error ? <p role="alert">Source unavailable: {error}</p> : null;
}
function Weather({ state }: { state: Remote<ContextWeather> }) {
  const weather = state.data;
  return <article className="evidence-panel" aria-label="District forecast">
    <h3>District forecast</h3><ResourceState {...state} />
    {weather && <>
      <p><strong className="evidence-mode">{weather.mode} · {weather.freshness}</strong> · {weather.provider}</p>
      {weather.error && <p className="evidence-warning">{weather.error}</p>}
      <dl className="context-metadata"><dt>Forecast begins</dt><dd>{time(weather.source_observation_time)}</dd><dt>Retrieved</dt><dd>{time(weather.retrieved_at || weather.last_success)}</dd></dl>
      {weather.daily?.time.length ? <div className="evidence-table-scroll"><table><caption>Daily forecast · Asia/Kathmandu</caption><thead><tr><th scope="col">Date</th><th scope="col">Rainfall (mm)</th><th scope="col">Max temp (°C)</th></tr></thead>
        <tbody>{weather.daily.time.map((date, i) => <tr key={date}><th scope="row">{date}</th><td>{weather.daily?.precipitation_sum[i] ?? "Unknown"}</td><td>{weather.daily?.temperature_2m_max[i] ?? "Unknown"}</td></tr>)}</tbody></table></div> : <p>No forecast values available.</p>}
      <p className="evidence-note">{weather.attribution}</p>
    </>}
    <p className="evidence-note">Forecast rainfall is not observed river flow or a prediction of a glacial-lake outburst.</p>
  </article>;
}
function Population({ state }: { state: Remote<PopulationContext> }) {
  const population = state.data;
  return <article className="evidence-panel" aria-label="District population context">
    <h3>District population context</h3><ResourceState {...state} />
    {population && <>
      <p className="evidence-number">{population.population != null && Number.isFinite(population.population) ? Math.round(population.population).toLocaleString("en-US") + " people" : "Population unavailable"}</p>
      <dl className="context-metadata"><dt>Status</dt><dd>{population.status}</dd><dt>Product year</dt><dd>{population.year ?? "Unknown"}</dd><dt>Covered cells</dt><dd>{population.valid_cells?.toLocaleString("en-US") ?? "Unknown"}</dd><dt>Method</dt><dd>{population.method || "Unavailable"}</dd><dt>Source</dt><dd><Value value={population.source} /></dd></dl>
      <p className="evidence-note">{population.attribution}</p><p className="evidence-note">{population.limitations}</p>
    </>}
    <p className="evidence-warning">Modelled district total for geographic context. This is not a count of people exposed to a flood.</p>
  </article>;
}
const initialFilters = { q: "", country: "", basin: "", districtOnly: false };
export default function EvidenceExplorer({ initialDistrict }: { initialDistrict?: string } = {}) {
  const id = useId();
  const catalog = useContextResource<ContextCatalog>("/public/context/catalog");
  const [district, setDistrict] = useState("");
  const [kind, setKind] = useState<"lakes" | "events">("lakes");
  const [draft, setDraft] = useState(initialFilters);
  const [filters, setFilters] = useState(initialFilters);
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState("");
  useEffect(() => {
    const districts = catalog.data?.districts;
    const wanted = initialDistrict?.trim().toLowerCase();
    if (districts?.length) setDistrict(current => current || districts.find(d => d.id.toLowerCase() === wanted || d.name.toLowerCase() === wanted)?.id || districts.find(d => d.id.toLowerCase() === "rasuwa" || d.name.toLowerCase() === "rasuwa")?.id || districts[0].id);
  }, [catalog.data, initialDistrict]);
  const parameters = new URLSearchParams({ q: filters.q, country: filters.country, basin: filters.basin, offset: String(offset), limit: "50" });
  if (filters.districtOnly && district) parameters.set("district", district);
  const records = useContextResource<ContextPage>(`/public/context/${kind}?${parameters}`);
  const weather = useContextResource<ContextWeather>(district ? `/public/context/weather/${encodeURIComponent(district)}` : null);
  const population = useContextResource<PopulationContext>(district ? `/public/context/population/${encodeURIComponent(district)}` : null);
  const chosen = records.data?.items.find(record => record.id === selected);
  const label = kind === "lakes" ? "Glacial-lake inventory" : "Historical events";
  function apply(event: FormEvent) { event.preventDefault(); setOffset(0); setSelected(""); setFilters({ ...draft }); }
  return <section id="evidence-context" className="evidence-explorer" aria-labelledby={`${id}-heading`}>
    <div className="evidence-heading"><div><span className="eyebrow accent">Evidence before action</span><h2 id={`${id}-heading`}>Explore district evidence</h2><p>Inspect geographic context, historical records and forecast provenance before preparing a reviewed notice.</p></div></div>
    <ResourceState {...catalog} />
    {catalog.data && <>
      <div className="evidence-sources">{catalog.data.sources.map(source => <article className="evidence-panel" key={source.id}><h3>{source.name}</h3><p><strong>{source.status}</strong>{source.count != null ? ` · ${source.count.toLocaleString("en-US")} records` : ""}</p><p>Source date / coverage: {source.source_date || "Unknown"}</p><p className="evidence-note">{source.attribution}</p><p className="evidence-note">{source.limitations}</p></article>)}</div>
      <p className="evidence-note">{catalog.data.limitations}</p>
      <div className="evidence-district"><label htmlFor={`${id}-district`}>District context</label><select id={`${id}-district`} value={district} onChange={event => { setDistrict(event.target.value); if (filters.districtOnly) { setOffset(0); setSelected(""); } }} disabled={!catalog.data.districts.length}><option value="" disabled>Select a district</option>{catalog.data.districts.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}</select></div>
      {!catalog.data.districts.length && <p>No district boundaries available for weather and population context.</p>}
    </>}
    {district && <div className="evidence-context-grid"><Weather state={weather} /><Population state={population} /></div>}
    <div className="evidence-tabs" role="group" aria-label="Evidence dataset">
      <button type="button" aria-pressed={kind === "lakes"} onClick={() => { setKind("lakes"); setOffset(0); setSelected(""); }}>Glacial-lake inventory</button>
      <button type="button" aria-pressed={kind === "events"} onClick={() => { setKind("events"); setOffset(0); setSelected(""); }}>Historical events</button>
    </div>
    <form onSubmit={apply} className="evidence-filters" aria-label="Filter contextual records">
      <label htmlFor={`${id}-search`}>Search records<input id={`${id}-search`} value={draft.q} maxLength={120} onChange={event => setDraft({ ...draft, q: event.target.value })} placeholder="Name or source ID" /></label>
      <label htmlFor={`${id}-country`}>Country<input id={`${id}-country`} value={draft.country} maxLength={80} onChange={event => setDraft({ ...draft, country: event.target.value })} placeholder="All countries" /></label>
      <label htmlFor={`${id}-basin`}>Basin<input id={`${id}-basin`} value={draft.basin} maxLength={80} onChange={event => setDraft({ ...draft, basin: event.target.value })} placeholder="All basins" /></label>
      <label className="evidence-checkbox"><input type="checkbox" checked={draft.districtOnly} disabled={!district} onChange={event => setDraft({ ...draft, districtOnly: event.target.checked })} />Limit records to selected district</label><button type="submit">Apply filters</button>
    </form>
    <ResourceState {...records} />
    {records.data && <>
      <div className="evidence-page-controls"><p aria-live="polite">{records.data.total ? `${offset + 1}–${Math.min(offset + records.data.items.length, records.data.total)} of ${records.data.total.toLocaleString("en-US")} records` : "No matching records"}</p><div><button type="button" disabled={offset === 0} onClick={() => { setOffset(Math.max(0, offset - 50)); setSelected(""); }}>Previous page</button><button type="button" disabled={offset + records.data.items.length >= records.data.total} onClick={() => { setOffset(offset + 50); setSelected(""); }}>Next page</button></div></div>
      {!records.data.items.length ? <p>No records are available for these filters. Try a broader search or another dataset.</p> : <>
        <ContextMap records={records.data.items} selected={selected} onSelect={setSelected} kind={label} />
        <p className="evidence-note">Map shows {records.data.items.filter(mapped).length} located records on this page. The list below includes records without coordinates. District membership uses geographic boundaries; basins are not flood inundation zones.</p>
        <ul className="evidence-records" aria-label={`${label} results`}>{records.data.items.map(record => <li key={record.id}><button type="button" aria-pressed={selected === record.id} onClick={() => setSelected(record.id)}><strong>{record.name || record.id}</strong><span>{record.country || "Country unknown"} · {record.basin || "Basin unknown"}{kind === "events" ? ` · ${record.date || record.year || "Date unknown"}` : ""}</span><small>{record.id}{!mapped(record) ? " · Unmapped: coordinates unavailable" : ""}</small></button></li>)}</ul>
      </>}
      {chosen && <article className="evidence-panel evidence-detail" aria-label="Selected record details"><h3>{chosen.name || chosen.id}</h3><dl className="context-metadata"><dt>Source ID</dt><dd>{chosen.id}</dd><dt>Source date / coverage</dt><dd>{chosen.source_date || "Unknown"}</dd><dt>Attribution</dt><dd>{chosen.attribution}</dd>{kind === "events" && <><dt>Event date</dt><dd>{chosen.date || chosen.year || "Unknown"} · precision: {chosen.date_precision || "Unknown"}</dd><dt>Recorded impact</dt><dd>{chosen.impact || "Unknown"}</dd></>}</dl><details><summary>All retained source attributes</summary><dl className="context-metadata">{Object.entries(chosen.properties).map(([key, value]) => <div key={key}><dt>{key}</dt><dd><Value value={value} /></dd></div>)}</dl></details></article>}
    </>}
  </section>;
}
