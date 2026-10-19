"use client";

import { ArrowRight, ClipboardList, Database, Map, ShieldCheck, Users, Workflow, Bell, type LucideIcon } from "lucide-react";
import { npt } from "@/lib/api";
import type { StaffRole } from "./operations-shell";

type Props = {
  role: StaffRole; loading: boolean; system: Record<string, unknown>;
  reports: { id: string; category: string; region: string; status: string; created_at: string }[];
  sources: { id: string; enabled: boolean; state: { provider: string; mode: string; health: string } }[];
  userCount: number; jurisdictionCount: number; onNavigate: (section: string) => void;
};

export default function OperationsOverview({ role, loading, system, reports, sources, userCount, jurisdictionCount, onNavigate }: Props) {
  const pending = reports.filter(report => (role === "admin" ? ["Submitted"] : ["Escalated", "Field verification requested"]).includes(report.status)).length;
  const metrics: { label: string; value: number; detail: string; icon: LucideIcon; section: string }[] = role === "admin" ? [
    { label: "Citizen reports", value: Number(system.reports || 0), detail: `${pending} awaiting review`, icon: ClipboardList, section: "reports" },
    { label: "Monitored lakes", value: Number(system.lakes || 0), detail: "Imported lake inventory", icon: Map, section: "monitoring" },
    { label: "Staff accounts", value: userCount, detail: "Accounts and jurisdictions", icon: Users, section: "users" },
    { label: "Enabled sources", value: sources.filter(source => source.enabled).length, detail: `${sources.length} configured providers`, icon: Database, section: "providers" },
  ] : [
    { label: "Field reports", value: Number(system.reports || 0), detail: `${pending} awaiting review`, icon: ClipboardList, section: "reports" },
    { label: "Incidents", value: Number(system.incidents || 0), detail: "Verified incident records", icon: Workflow, section: "incidents" },
    { label: "Alerts", value: Number(system.alerts || 0), detail: "All publication stages", icon: Bell, section: "alerts" },
    { label: "Jurisdictions", value: jurisdictionCount, detail: "Assigned regions", icon: Map, section: "monitoring" },
  ];
  return <div className="ops-overview">
    <div className="ops-metric-grid" aria-label="Workspace summary">{metrics.map(metric => <button className="ops-metric-card" key={metric.label} onClick={() => onNavigate(metric.section)}><div className="ops-metric-top"><span>{metric.label}</span><metric.icon size={19} aria-hidden="true" /></div><strong>{loading ? "—" : metric.value.toLocaleString()}</strong><div className="ops-metric-bottom"><small>{loading ? "Loading workspace…" : metric.detail}</small><ArrowRight size={15} aria-hidden="true" /></div></button>)}</div>
    <section className="ops-priority-card"><div className="ops-priority-icon"><ShieldCheck size={26} aria-hidden="true" /></div><div><span className="ops-kicker">Review queue</span><h2>{loading ? "Preparing your workspace" : pending ? `${pending} report${pending === 1 ? "" : "s"} ready for review` : "Your review queue is clear"}</h2><p>{role === "admin" ? "Review evidence, record your decision and escalate credible observations to the assigned government team." : "Verify field evidence and coordinate the next response within your assigned regions."}</p></div><button className="primary" onClick={() => onNavigate("reports")}>Review reports <ArrowRight size={16} aria-hidden="true" /></button></section>
    <div className="ops-overview-grid">
      <section className="ops-surface"><div className="ops-surface-heading"><div><h2>Recent reports</h2><p>Latest observations in your workspace</p></div><button className="ops-text-button" onClick={() => onNavigate("reports")}>View all <ArrowRight size={15} aria-hidden="true" /></button></div>
        {loading ? <p className="ops-empty-inline">Loading reports…</p> : !reports.length ? <div className="ops-empty-state"><ClipboardList size={30} aria-hidden="true" /><h3>No reports yet</h3><p>New citizen observations will appear here for review.</p></div> : <div className="ops-recent-list">{[...reports].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 5).map(report => <button key={report.id} onClick={() => onNavigate("reports")}><span className="ops-report-icon"><ClipboardList size={18} aria-hidden="true" /></span><span><strong>{report.category.replaceAll("_", " ")}</strong><small>{report.region} · {npt(report.created_at)}</small></span><span className="ops-status-pill">{report.status}</span><ArrowRight size={15} aria-hidden="true" /></button>)}</div>}
      </section>
      <section className="ops-surface"><div className="ops-surface-heading"><div><h2>{role === "admin" ? "Data sources" : "Response workflow"}</h2><p>{role === "admin" ? "Availability and data modes" : "Keep each decision accountable"}</p></div>{role === "admin" && <button className="ops-text-button" onClick={() => onNavigate("providers")}>Manage <ArrowRight size={15} aria-hidden="true" /></button>}</div>
        {role === "admin" ? loading ? <p className="ops-empty-inline">Loading sources…</p> : !sources.length ? <p className="ops-empty-inline">No data sources configured.</p> : <ul className="ops-source-list">{sources.slice(0, 4).map(source => <li key={source.id}><span className={`ops-source-dot${source.enabled && source.state.health === "ok" ? " is-healthy" : ""}`} /><div><strong>{source.state.provider}</strong><small>{source.enabled ? source.state.health : "disabled"}</small></div><span className="ops-status-pill">{source.state.mode}</span></li>)}</ul> : <ol className="ops-workflow-list"><li><strong>Verify field evidence</strong><span>Review escalated reports and record your findings.</span></li><li><strong>Coordinate a response</strong><span>Track incident actions and prepare clear instructions.</span></li><li><strong>Review before publication</strong><span>Approve each notice before it becomes public.</span></li></ol>}
      </section>
    </div>
    {role === "admin" && <section className="ops-quick-links" aria-label="Administration shortcuts"><button onClick={() => onNavigate("users")}><Users size={21} aria-hidden="true" /><span><strong>Manage access</strong><small>Staff accounts and jurisdictions</small></span><ArrowRight size={17} aria-hidden="true" /></button><button onClick={() => onNavigate("audit-logs")}><ShieldCheck size={21} aria-hidden="true" /><span><strong>Review activity</strong><small>Recorded actions and decisions</small></span><ArrowRight size={17} aria-hidden="true" /></button><button onClick={() => onNavigate("settings")}><Database size={21} aria-hidden="true" /><span><strong>Configure rules</strong><small>Thresholds and alert templates</small></span><ArrowRight size={17} aria-hidden="true" /></button></section>}
    <p className="ops-demo-notice"><ShieldCheck size={16} aria-hidden="true" />Demonstration workspace. Assessments are experimental; local publications are not official emergency broadcasts.</p>
  </div>;
}
