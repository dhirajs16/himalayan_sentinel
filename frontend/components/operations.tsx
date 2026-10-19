"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Mountain, Search, ShieldCheck } from "lucide-react";
import { api, API, getAccessToken, npt, setAccessToken } from "@/lib/api";
import LakeMonitor from "./lake-monitor";
import EvidenceExplorer from "./evidence-explorer";
import OperationsShell, { workspaceSections } from "./operations-shell";
import OperationsOverview from "./operations-overview";
import type { PublicAlert } from "@/lib/types";

type User = { id: string; email: string; role: "admin" | "government"; jurisdictions: string[]; active: boolean };
type Report = { id: string; region: string; description: string; category: string; status: string; lat: number; lng: number; observed_at: string; created_at: string };
type Incident = { id: string; report_id: string; region: string; status: string; severity: string; evidence_summary: string; actions: string[] };
type StaffAlert = PublicAlert & { incident_id: string; disaster_type: string; resources: string[] };
type Source = { id: string; enabled: boolean; state: { provider: string; mode: string; health: string; freshness?: string; last_success?: string; attribution: string; error?: string } };
const reasonDefault = "Reviewed available evidence for this demonstration.";

function Evidence({ report }: { report: Report }) {
  const [url, setUrl] = useState(""); const [error, setError] = useState("");
  useEffect(() => { let objectUrl = ""; let active = true;
    fetch(`${API}/api/v1/staff/reports/${report.id}/media`, { headers: { Authorization: `Bearer ${getAccessToken()}` } })
      .then(r => { if (!r.ok) throw new Error("Evidence unavailable or access denied"); return r.blob(); })
      .then(b => { objectUrl = URL.createObjectURL(b); if (active) setUrl(objectUrl); else URL.revokeObjectURL(objectUrl); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [report.id]);
  return <div className="evidence-view">{error ? <p role="alert">{error}</p> : url ? <img src={url} alt={`Private evidence for ${report.category.replaceAll("_", " ")} observation`} /> : <p role="status">Loading private evidence…</p>}<small>Sanitized image · exact location restricted to authorized staff.</small><p>{report.lat.toFixed(4)}, {report.lng.toFixed(4)} · Observed {npt(report.observed_at)}</p></div>;
}

export default function Operations() {
  const [user, setUser] = useState<User | null>(null); const [restoring, setRestoring] = useState(true);
  const [error, setError] = useState(""); const [message, setMessage] = useState(""); const [busy, setBusy] = useState(false);
  const [tab, setTab] = useState("overview"); const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true); const [resourceLoading, setResourceLoading] = useState(false);
  const [resourceVersion, setResourceVersion] = useState(0);
  const [reportSearch, setReportSearch] = useState(""); const [reportStatus, setReportStatus] = useState("all");
  const [incidents, setIncidents] = useState<Incident[]>([]); const [alerts, setAlerts] = useState<StaffAlert[]>([]);
  const [sources, setSources] = useState<Source[]>([]); const [users, setUsers] = useState<User[]>([]);
  const [system, setSystem] = useState<Record<string, unknown>>({}); const [records, setRecords] = useState<unknown[]>([]);
  const [evidenceId, setEvidenceId] = useState(""); const [reason, setReason] = useState(reasonDefault);
  const [compose, setCompose] = useState<Incident | null>(null); const [editing, setEditing] = useState<StaffAlert | null>(null);
  const [aiText, setAiText] = useState(""); const [template, setTemplate] = useState("Follow official local notices. Avoid rivers and damaged crossings. Prepare essential supplies.");
  useEffect(() => { api<{ access_token: string; user: User }>("/auth/refresh", { method: "POST" }).then(r => { setAccessToken(r.access_token); setUser(r.user); }).catch(() => {}).finally(() => setRestoring(false)); }, []);
  const load = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    const prefix = user.role === "admin" ? "/admin" : "/government";
    try {
      const [reportData, dashboard] = await Promise.all([api<{ items: Report[] }>(`${prefix}/reports`), api<Record<string, unknown>>(`${prefix}/dashboard`)]);
      setReports(reportData.items); setSystem(dashboard);
      if (user.role === "government") {
        const [i, a, t] = await Promise.all([api<{ items: Incident[] }>("/government/incidents"), api<{ items: StaffAlert[] }>("/government/alerts"), api<{ safety_instructions: string }>("/government/alert-template")]);
        setIncidents(i.items); setAlerts(a.items); setTemplate(t.safety_instructions);
      } else {
        const [s, u] = await Promise.all([api<{ items: Source[] }>("/admin/data-sources"), api<{ items: User[] }>("/admin/users")]);
        setSources(s.items); setUsers(u.items);
      }
    } catch (e) { setError((e as Error).message); } finally { setLoading(false); }
  }, [user]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!user) return;
    const syncSection = () => {
      const requested = window.location.hash.slice(1);
      setTab(workspaceSections(user.role).some(item => item.id === requested) ? requested : "overview");
      setRecords([]); setMessage(""); setError(""); setEvidenceId(""); window.scrollTo(0, 0);
    };
    syncSection(); window.addEventListener("hashchange", syncSection);
    return () => window.removeEventListener("hashchange", syncSection);
  }, [user]);
  useEffect(() => {
    if (user?.role !== "admin" || !["audit-logs", "sync-runs", "deliveries", "data-quality"].includes(tab)) { setResourceLoading(false); return; }
    let active = true; setResourceLoading(true); setRecords([]);
    api<{ items?: unknown[]; datasets?: unknown[] }>(`/admin/${tab}`)
      .then(result => { if (active) setRecords(result.items || result.datasets || []); })
      .catch(e => { if (active) setError((e as Error).message); })
      .finally(() => { if (active) setResourceLoading(false); });
    return () => { active = false; };
  }, [tab, user, resourceVersion]);
  function navigate(section: string) {
    if (window.location.hash.slice(1) !== section) window.location.hash = section;
    else setTab(section);
  }
  async function refreshWorkspace() { setError(""); await load(); setResourceVersion(value => value + 1); }
  async function login(form: FormData) { setBusy(true); setError(""); try { const result = await api<{ access_token: string; user: User }>("/auth/login", { method: "POST", body: JSON.stringify({ email: form.get("email"), password: form.get("password") }) }); setAccessToken(result.access_token); setUser(result.user); } catch (e) { setError((e as Error).message); } finally { setBusy(false); } }
  async function logout() { try { await api("/auth/logout", { method: "POST" }); } catch {} setAccessToken(""); setUser(null); setReports([]); setIncidents([]); setAlerts([]); setSources([]); setUsers([]); setRecords([]); setMessage(""); setError(""); setCompose(null); setEditing(null); setEvidenceId(""); setAiText(""); }
  async function mutate(path: string, body: unknown, method = "POST", confirmation = "") {
    if (confirmation && !window.confirm(confirmation)) return false;
    setBusy(true); setError(""); setMessage("");
    try { await api(path, { method, body: JSON.stringify(body) }); setMessage("Saved. Audit history updated."); await load(); return true; }
    catch (e) { setError((e as Error).message); return false; } finally { setBusy(false); }
  }
  async function draftAI(incident: Incident) { setBusy(true); setError(""); try { const draft = await api<{ summary: string; source: string }>(`/government/incidents/${incident.id}/ai-draft`, { method: "POST" }); setAiText(draft.summary); setMessage(`AI-assisted draft from ${draft.source}. Review before approval.`); } catch (e) { setError((e as Error).message); } finally { setBusy(false); } }
  async function saveAlert(form: FormData) {
    if (!compose) return;
    const body = { incident_id: compose.id, title: form.get("title"), disaster_type: form.get("disaster_type"), severity: form.get("severity"),
      description: form.get("description"), evidence_summary: form.get("evidence_summary"), safety_instructions: form.get("safety_instructions"), resources: [],
      effective_at: new Date(String(form.get("effective_at"))).toISOString(), expires_at: new Date(String(form.get("expires_at"))).toISOString() };
    if (await mutate(editing ? `/government/alerts/${editing.id}` : "/government/alerts", body, editing ? "PUT" : "POST")) { setCompose(null); setEditing(null); setAiText(""); navigate("alerts"); }
  }
  async function exportIncident(incident: Incident) {
    try { const data = await api(`/government/incidents/${incident.id}/export`); const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })); const a = document.createElement("a"); a.href = url; a.download = `incident-${incident.id}.json`; a.click(); URL.revokeObjectURL(url); }
    catch (e) { setError((e as Error).message); }
  }
  const localDate = (value: string) => { const date = new Date(value); return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16); };
  const filteredReports = reports.filter(report => (reportStatus === "all" || report.status === reportStatus) && `${report.category} ${report.region} ${report.description} ${report.id}`.replaceAll("_", " ").toLowerCase().includes(reportSearch.toLowerCase()));
  if (restoring || !user) return <div className="ops-login-page">
    <header className="ops-login-topbar"><Link href="/" className="ops-login-brand"><Mountain size={25} aria-hidden="true" /><strong>Himalayan Sentinel</strong></Link><Link href="/"><ArrowLeft size={16} aria-hidden="true" />Public dashboard</Link></header>
    <main className="operations ops-login-content"><div className="ops-login-heading"><span className="ops-login-emblem"><ShieldCheck size={28} aria-hidden="true" /></span><span className="ops-kicker">Authorized operations</span><h1>Staff sign in</h1><p>Your workspace for evidence, verification and accountable decisions.</p></div>
    {restoring ? <p role="status" className="ops-empty-inline">Checking session?</p> : <form action={login} className="ops-surface stack-form ops-login-form"><h2>Sign in to your assigned role</h2>{error && <p role="alert" className="error-message">{error}</p>}<label>Email<input type="email" name="email" required autoComplete="username" placeholder="you@organization.org" /></label><label>Password<input type="password" name="password" required autoComplete="current-password" /></label><button className="primary" disabled={busy}>{busy ? "Signing in?" : "Sign in"}</button><p className="ops-form-help">Use your assigned admin or government account. Your role and jurisdictions determine workspace access.</p></form>}
    <p className="ops-login-footnote"><ShieldCheck size={14} aria-hidden="true" />Private evidence ? Human verification ? Recorded decisions</p></main>
  </div>;
  const currentSection = workspaceSections(user.role).find(section => section.id === tab) || workspaceSections(user.role)[0];
  const pendingCount = reports.filter(report => (user.role === "admin" ? ["Submitted"] : ["Escalated", "Field verification requested"]).includes(report.status)).length;
  return <OperationsShell role={user.role} email={user.email} section={tab} pendingCount={pendingCount} busy={busy || loading || resourceLoading} onNavigate={navigate} onRefresh={refreshWorkspace} onLogout={logout}>
    <div className="ops-page-heading"><div><span className="ops-kicker">{currentSection.group}</span><h1>{currentSection.title}</h1><p>{currentSection.description}</p></div>{tab === "reports" && <span className="ops-status-pill">{pendingCount} awaiting review</span>}</div>
    {error && <p role="alert" className="error-message">{error}</p>}{message && <p role="status" className="success">{message}</p>}
    {loading && tab !== "overview" && <p role="status" className="ops-loading">Updating workspace?</p>}
    {user.role === "government" && <p className="notice">Assigned jurisdictions: {user.jurisdictions.join(", ")}. Local demo publications are not official emergency broadcasts.</p>}
    {tab === "overview" && <OperationsOverview role={user.role} loading={loading} system={system} reports={reports} sources={sources} userCount={users.length} jurisdictionCount={user.jurisdictions.length} onNavigate={navigate} />}
      {tab === "reports" && <section className="card panel"><h2>{user.role === "admin" ? "Citizen moderation queue" : "Escalated field reports"}</h2><label>Review reason<textarea value={reason} onChange={e => setReason(e.target.value)} minLength={5} maxLength={2000} /></label><div className="ops-table-toolbar"><label className="ops-search"><Search size={17} aria-hidden="true" /><input aria-label="Search reports" value={reportSearch} onChange={e => setReportSearch(e.target.value)} placeholder="Search region, category or report?" /></label><select aria-label="Filter reports by status" value={reportStatus} onChange={e => setReportStatus(e.target.value)}><option value="all">All statuses</option>{[...new Set(reports.map(report => report.status))].map(status => <option key={status}>{status}</option>)}</select><span>{filteredReports.length} report{filteredReports.length === 1 ? "" : "s"}</span></div>{!loading && !filteredReports.length && <div className="ops-empty-state"><ShieldCheck size={30} aria-hidden="true" /><h3>{reports.length ? "No matching reports" : "No reports in your queue"}</h3><p>{reports.length ? "Try another search or choose a different status." : "New observations will appear here when they are ready for review."}</p>{reports.length > 0 && <button onClick={() => { setReportSearch(""); setReportStatus("all"); }}>Clear filters</button>}</div>}{filteredReports.map(r => <article className="queue-item" key={r.id}><div className="section-title"><h3>{r.category.replaceAll("_", " ")} · {r.region}</h3><span className="demo-tag">{r.status}</span></div><p>{r.description}</p><small>{npt(r.created_at)} · {r.id}</small><div className="button-row"><button onClick={() => setEvidenceId(evidenceId === r.id ? "" : r.id)}>Inspect evidence</button>{user.role === "admin" && r.status === "Submitted" && <><button disabled={busy || reason.length < 5} onClick={() => mutate(`/admin/reports/${r.id}/review`, { action: "escalate", reason })}>Escalate to government</button><button disabled={busy || reason.length < 5} onClick={() => mutate(`/admin/reports/${r.id}/review`, { action: "reject", reason }, "POST", "Reject this report? The reason will be recorded.")}>Reject</button></>}{user.role === "government" && ["Escalated", "Field verification requested"].includes(r.status) && <><button className="primary" disabled={busy || reason.length < 5} onClick={() => mutate(`/government/reports/${r.id}/review`, { action: "confirm", reason, severity: "High" }, "POST", "Confirm this incident based on reviewed evidence? This is a recorded government decision.")}>Confirm incident</button><button disabled={busy} onClick={() => mutate(`/government/reports/${r.id}/review`, { action: "request_verification", reason })}>Request field verification</button><button disabled={busy} onClick={() => mutate(`/government/reports/${r.id}/review`, { action: "reject", reason }, "POST", "Reject this report? Review reason will be recorded.")}>Reject</button></>}</div>{evidenceId === r.id && <Evidence report={r} />}</article>)}</section>}
      {tab === "incidents" && <section className="card panel"><h2>Incident response queue</h2>{!incidents.length && <p className="empty">Confirm an escalated report to open an incident.</p>}{incidents.map(i => <article className="queue-item" key={i.id}><h3>{i.region} · {i.severity} · {i.status}</h3><p>{i.evidence_summary}</p><div className="button-row"><button onClick={() => { setCompose(i); setEditing(null); setAiText(""); }}>Compose alert</button><button onClick={() => exportIncident(i)}>Export summary</button>{i.status !== "Resolved" && <button disabled={busy} onClick={() => mutate(`/government/incidents/${i.id}`, { status: "Resolved", actions: i.actions, reason }, "PATCH", "Close this incident? Resolve published alerts first.")}>Close incident</button>}</div><details><summary>Response actions and timeline</summary>{["Field team requested", "Local authority contacted", "Public instructions reviewed"].map(action => <label className="check" key={action}><input type="checkbox" checked={i.actions.includes(action)} disabled={busy || i.status === "Resolved"} onChange={e => mutate(`/government/incidents/${i.id}`, { status: "Responding", actions: e.target.checked ? [...i.actions, action] : i.actions.filter(a => a !== action), reason }, "PATCH")} />{action}</label>)}<button onClick={async () => { try { const data = await api(`/government/incidents/${i.id}/export`); setRecords([data]); } catch (e) { setError((e as Error).message); } }}>Load incident timeline</button></details></article>)}{records.length > 0 && <details><summary>Incident timeline and audit</summary><pre>{JSON.stringify(records, null, 2)}</pre></details>}</section>}
      {compose && user.role === "government" && <section className="card panel"><h2>{editing ? "Edit alert · approval will reset" : "Alert composer"}</h2><p>Incident {compose.id}. Effective/expiry fields use your device timezone and are stored as UTC.</p><p><Link href={`/evidence?district=${encodeURIComponent(compose.region)}`} target="_blank" rel="noopener noreferrer">Review district sources and current forecast</Link> before deciding which facts belong in this notice. Geographic context does not establish a causal link to this incident.</p><button disabled={busy} onClick={() => draftAI(compose)}>Generate AI-assisted draft</button><form action={saveAlert} className="stack-form" key={editing?.id || compose.id}><label>Title<input name="title" minLength={5} maxLength={160} required defaultValue={editing?.title || `Monitoring notice for ${compose.region}`} /></label><div className="form-row"><label>Disaster type<select name="disaster_type" defaultValue={editing?.disaster_type || "Flood"}>{["Flood", "GLOF", "Landslide", "Other"].map(x => <option key={x}>{x}</option>)}</select></label><label>Severity<select name="severity" defaultValue={editing?.severity || compose.severity}>{["Low", "Moderate", "High", "Critical"].map(x => <option key={x}>{x}</option>)}</select></label></div><label>Public description<textarea name="description" key={aiText || "description"} required minLength={10} maxLength={4000} defaultValue={aiText || editing?.description || "Local observation confirmed by the demo official. Monitor local authority updates."} /></label><label>Evidence summary · exclude reporter identity and sensitive coordinates<textarea name="evidence_summary" required minLength={5} defaultValue={editing?.evidence_summary || compose.evidence_summary} /></label><label>Safety instructions<textarea name="safety_instructions" minLength={10} required defaultValue={editing?.safety_instructions || template} /></label><div className="form-row"><label>Effective<input type="datetime-local" name="effective_at" required defaultValue={localDate(editing?.effective_at || new Date().toISOString())} /></label><label>Expires<input type="datetime-local" name="expires_at" required defaultValue={localDate(editing?.expires_at || new Date(Date.now() + 86400000).toISOString())} /></label></div><div className="button-row"><button className="primary" disabled={busy}>Save draft</button><button type="button" onClick={() => { setCompose(null); setEditing(null); }}>Close composer</button></div></form></section>}
      {tab === "alerts" && <section className="card panel"><h2>Alert approval and publication</h2><p>Draft → Pending approval → Approved → Published → Resolved. Every edited publication requires fresh approval.</p><label>Decision / resolution reason<textarea value={reason} onChange={e => setReason(e.target.value)} /></label>{!alerts.length && <p className="empty">No alerts drafted yet.</p>}{alerts.map(a => <article key={a.id} className="queue-item"><div className="section-title"><h3>{a.title}</h3><span className="demo-tag">{a.status}</span></div><p>{a.description}</p><p>{a.safety_instructions}</p><small>Expires {npt(a.expires_at)} · {a.severity}</small><div className="button-row">{["Draft", "Pending approval", "Approved", "Published", "Updated"].includes(a.status) && <button onClick={() => { setCompose(incidents.find(i => i.id === a.incident_id) || null); setEditing(a); setAiText(""); }}>Edit</button>}{(a.status === "Draft" ? ["submit"] : a.status === "Pending approval" ? ["approve"] : a.status === "Approved" ? ["publish"] : ["Published", "Updated"].includes(a.status) ? ["resolve", "cancel"] : []).map(action => <button key={action} className="primary" disabled={busy || reason.length < 5} onClick={() => mutate(`/government/alerts/${a.id}/${action}`, { reason }, "POST", `${action.toUpperCase()} this alert? This decision is recorded and publication appears on the public dashboard.`)}>{action}</button>)}<button onClick={async () => { try { const h = await api<{ items: unknown[] }>(`/government/alerts/${a.id}/history`); setRecords(h.items); } catch (e) { setError((e as Error).message); } }}>History</button></div></article>)}{records.length > 0 && <details><summary>Selected alert history</summary><pre>{JSON.stringify(records, null, 2)}</pre></details>}</section>}
      {tab === "monitoring" && <><EvidenceExplorer /><LakeMonitor /></>}
      {tab === "providers" && <section><h2>Provider health and freshness</h2><div className="provider-grid">{sources.map(s => <article className="card panel" key={s.id}><span className="eyebrow">{s.state.mode} · {s.enabled ? "enabled" : "disabled"}</span><h3>{s.state.provider}</h3><p>Health: {s.state.health} · Freshness: {s.state.freshness || "unknown"}</p><p>Last success: {npt(s.state.last_success || null)}</p><p>{s.state.error}</p><small>{s.state.attribution}</small><div className="button-row"><button disabled={busy} onClick={() => mutate(`/admin/data-sources/${s.id}/sync`, { reason })}>Retry sync</button><button disabled={busy} onClick={() => mutate(`/admin/data-sources/${s.id}/${s.enabled ? "disable" : "enable"}`, { reason }, "POST", "Change provider availability? Risk indicators may become stale.")}>{s.enabled ? "Disable" : "Enable"}</button></div></article>)}</div></section>}
      {tab === "users" && <section className="card panel"><h2>Accounts and jurisdiction assignments</h2>{users.map(u => <form key={u.id} className="queue-item stack-form" action={form => mutate(`/admin/users/${u.id}`, { active: form.get("active") === "true", jurisdictions: String(form.get("jurisdictions")).split(",").map(s => s.trim()).filter(Boolean) }, "PATCH", "Update account access and revoke its sessions?").then(() => {})}><b>{u.email} · {u.role}</b><label>Jurisdictions (comma-separated region IDs)<input name="jurisdictions" defaultValue={u.jurisdictions.join(", ")} /></label><label className="check"><input type="checkbox" name="active" value="true" defaultChecked={u.active} />Active account</label><button disabled={busy}>Save access</button></form>)}<details><summary>Create account</summary><form className="stack-form" action={form => mutate("/admin/users", { email: form.get("email"), password: form.get("password"), role: form.get("role"), jurisdictions: String(form.get("jurisdictions")).split(",").map(s => s.trim()).filter(Boolean) }).then(() => {})}><label>Email<input type="email" name="email" required /></label><label>Temporary password<input type="password" name="password" minLength={12} required /></label><label>Role<select name="role"><option value="government">government</option><option value="admin">admin</option></select></label><label>Jurisdictions<input name="jurisdictions" placeholder="rasuwa, dolakha" /></label><button disabled={busy}>Create account</button></form></details></section>}
      {tab === "settings" && <section className="card panel"><h2>Prototype rules and alert templates</h2><p>Version lake-rules-1.0 · weights are experimental. Changes apply on next scheduled recalculation.</p><form className="stack-form" action={form => mutate("/admin/risk-settings", { low_max: Number(form.get("low")), moderate_max: Number(form.get("moderate")), high_max: Number(form.get("high")) }, "PUT", "Change monitoring thresholds? Historical assessments retain their original thresholds.").then(() => {})}><label>Low maximum<input type="number" name="low" defaultValue={25} required /></label><label>Moderate maximum<input type="number" name="moderate" defaultValue={50} required /></label><label>High maximum<input type="number" name="high" defaultValue={75} required /></label><button disabled={busy}>Save thresholds</button></form><form className="stack-form" action={form => mutate("/admin/templates", { safety_instructions: form.get("safety") }, "PUT").then(() => {})}><label>Safety instruction template<textarea name="safety" defaultValue={template} required minLength={10} /></label><button disabled={busy}>Save template</button></form></section>}
      {["audit-logs", "sync-runs", "deliveries", "data-quality"].includes(tab) && <section className="card panel"><h2>{tab.replaceAll("-", " ")}</h2>{resourceLoading ? <p role="status">Loading…</p> : !records.length ? <p className="empty">No records yet.</p> : <div className="record-list">{records.map((r, index) => <details key={index}><summary>Record {index + 1} · {String((r as Record<string, unknown>).action || (r as Record<string, unknown>).provider || (r as Record<string, unknown>).path || (r as Record<string, unknown>).status || "details")}</summary><pre>{JSON.stringify(r, null, 2)}</pre></details>)}</div>}</section>}
  </OperationsShell>;
}
