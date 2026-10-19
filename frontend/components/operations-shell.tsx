"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  ArrowUpRight, Bell, ClipboardList, Database, FileClock, LayoutDashboard,
  LogOut, Map, Menu, Mountain, PanelLeftClose, PanelLeftOpen, RefreshCw,
  Send, Settings2, ShieldCheck, Users, Workflow, X, type LucideIcon,
} from "lucide-react";

export type StaffRole = "admin" | "government";
export type WorkspaceSection = { id: string; label: string; title: string; description: string; group: string; icon: LucideIcon };

export function workspaceSections(role: StaffRole): WorkspaceSection[] {
  const shared = [
    { id: "overview", label: "Overview", title: role === "admin" ? "System administration" : "Government workspace", description: "Your workspace at a glance. Review what needs attention and pick up where you left off.", group: "Workspace", icon: LayoutDashboard },
    { id: "reports", label: "Citizen reports", title: role === "admin" ? "Citizen reports" : "Field reports", description: role === "admin" ? "Review private citizen evidence and send credible observations for government verification." : "Review escalated observations within your assigned jurisdictions.", group: "Workspace", icon: ClipboardList },
  ];
  const monitoring = { id: "monitoring", label: "Lake monitoring", title: "Lake monitoring", description: "Explore the lake inventory, source evidence and experimental monitoring assessments.", group: "Workspace", icon: Map };
  return role === "admin" ? [...shared, monitoring,
    { id: "users", label: "Users & access", title: "Users & access", description: "Manage staff accounts, account access and jurisdiction assignments.", group: "Administration", icon: Users },
    { id: "providers", label: "Data providers", title: "Data providers", description: "Check source freshness and manage provider availability and synchronization.", group: "Administration", icon: Database },
    { id: "settings", label: "Rules & templates", title: "Rules & templates", description: "Manage experimental monitoring thresholds and public instruction templates.", group: "Administration", icon: Settings2 },
    { id: "audit-logs", label: "Audit log", title: "Audit log", description: "Review recorded staff actions and decisions.", group: "Activity & records", icon: FileClock },
    { id: "sync-runs", label: "Sync history", title: "Sync history", description: "Inspect data synchronization runs and recorded outcomes.", group: "Activity & records", icon: RefreshCw },
    { id: "deliveries", label: "Notification logs", title: "Notification logs", description: "Review mock notification delivery records for local publications.", group: "Activity & records", icon: Send },
    { id: "data-quality", label: "Data quality", title: "Data quality", description: "Inspect source schemas, geometry checks and data provenance.", group: "Activity & records", icon: ShieldCheck },
  ] : [...shared,
    { id: "incidents", label: "Incidents", title: "Incidents", description: "Coordinate verified incidents, response actions and alert preparation.", group: "Workspace", icon: Workflow },
    { id: "alerts", label: "Alerts", title: "Alerts", description: "Draft, review, approve and manage public notices.", group: "Workspace", icon: Bell }, monitoring,
  ];
}

type Props = {
  role: StaffRole; email: string; section: string; pendingCount: number;
  busy: boolean; onNavigate: (id: string) => void; onRefresh: () => void;
  onLogout: () => void; children: ReactNode;
};

export default function OperationsShell({ role, email, section, pendingCount, busy, onNavigate, onRefresh, onLogout, children }: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobile, setMobile] = useState(false);
  const [open, setOpen] = useState(false);
  const sidebar = useRef<HTMLElement>(null);
  const toggle = useRef<HTMLButtonElement>(null);
  const sections = workspaceSections(role);
  const current = sections.find(item => item.id === section) || sections[0];
  const roleLabel = role === "admin" ? "Administrator" : "Government officer";

  useEffect(() => {
    try { setCollapsed(localStorage.getItem("sentinel-sidebar-collapsed") === "true"); } catch {}
    const query = window.matchMedia("(max-width: 900px)");
    const update = () => { setMobile(query.matches); if (!query.matches) setOpen(false); };
    update(); query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (!mobile || !open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    sidebar.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const keyboard = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); setOpen(false); }
      if (event.key !== "Tab") return;
      const items = sidebar.current?.querySelectorAll<HTMLElement>('a[href], button:not([disabled])');
      if (!items?.length) return;
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", keyboard);
    return () => { document.body.style.overflow = previousOverflow; document.removeEventListener("keydown", keyboard); toggle.current?.focus(); };
  }, [mobile, open]);

  function toggleSidebar() {
    if (mobile) { setOpen(value => !value); return; }
    setCollapsed(value => { try { localStorage.setItem("sentinel-sidebar-collapsed", String(!value)); } catch {} return !value; });
  }

  return <div className={`ops-layout${collapsed ? " is-collapsed" : ""}${open ? " is-menu-open" : ""}`}>
    <a className="ops-skip" href="#workspace-content" onClick={event => { event.preventDefault(); document.getElementById("workspace-content")?.focus(); }}>Skip to workspace content</a>
    {open && mobile && <div className="ops-backdrop" aria-hidden="true" onClick={() => setOpen(false)} />}
    <aside ref={sidebar} id="workspace-sidebar" className="ops-sidebar" aria-label="Workspace navigation" role={mobile && open ? "dialog" : undefined} aria-modal={mobile && open ? true : undefined} inert={mobile && !open}>
      <div className="ops-sidebar-brand"><Link href="/" aria-label="Himalayan Sentinel public dashboard"><span className="ops-logo"><Mountain size={23} aria-hidden="true" /></span><span className="ops-sidebar-copy"><strong>Himalayan Sentinel</strong><small>Operations workspace</small></span></Link><button className="ops-mobile-close" onClick={() => setOpen(false)} aria-label="Close navigation"><X size={20} /></button></div>
      <div className="ops-role-label ops-sidebar-copy"><ShieldCheck size={14} aria-hidden="true" />{roleLabel}</div>
      <nav aria-label="Staff workspace" className="ops-navigation">
        {[...new Set(sections.map(item => item.group))].map(group => <div className="ops-nav-group" key={group}>
          <p className="ops-group-label ops-sidebar-copy">{group}</p>
          {sections.filter(item => item.group === group).map(item => <a key={item.id} href={`#${item.id}`} title={collapsed && !mobile ? item.label : undefined} aria-label={item.label} aria-current={section === item.id ? "page" : undefined} className={`ops-nav-link${section === item.id ? " is-current" : ""}`} onClick={event => { event.preventDefault(); onNavigate(item.id); setOpen(false); }}><item.icon size={19} aria-hidden="true" /><span className="ops-sidebar-copy">{item.label}</span>{item.id === "reports" && pendingCount > 0 && <span className="ops-nav-count ops-sidebar-copy" aria-hidden="true">{pendingCount}</span>}</a>)}
        </div>)}
      </nav>
      <div className="ops-sidebar-bottom"><Link href="/" className="ops-nav-link" title="Public dashboard"><ArrowUpRight size={19} aria-hidden="true" /><span className="ops-sidebar-copy">Public dashboard</span></Link><div className="ops-sidebar-note ops-sidebar-copy"><span className="ops-demo-dot" />Local demonstration<span>Human review at every step.</span></div></div>
    </aside>
    <div className="ops-main" inert={mobile && open} aria-hidden={mobile && open ? true : undefined}>
      <header className="ops-topbar">
        <div className="ops-topbar-start"><button ref={toggle} className="ops-icon-button" onClick={toggleSidebar} aria-label={mobile ? (open ? "Close navigation" : "Open navigation") : collapsed ? "Expand sidebar" : "Collapse sidebar"} aria-expanded={mobile ? open : !collapsed} aria-controls="workspace-sidebar">{mobile ? <Menu size={21} /> : collapsed ? <PanelLeftOpen size={21} /> : <PanelLeftClose size={21} />}</button><div className="ops-breadcrumb"><span>{role === "admin" ? "Administration" : "Government"}</span><span aria-hidden="true">/</span><strong>{current.label}</strong></div></div>
        <div className="ops-topbar-actions"><span className="ops-demo-badge">Demo workspace</span><button className="ops-icon-button" onClick={onRefresh} disabled={busy} aria-label="Refresh workspace" title="Refresh workspace"><RefreshCw size={18} className={busy ? "ops-spinning" : ""} /></button><div className="ops-account"><span className="ops-avatar" aria-hidden="true">{email.charAt(0).toUpperCase()}</span><div><strong>{roleLabel}</strong><small title={email}>{email}</small></div></div><button className="ops-signout" onClick={onLogout} aria-label="Sign out"><LogOut size={17} aria-hidden="true" /><span>Sign out</span></button></div>
      </header>
      <main id="workspace-content" tabIndex={-1} className="operations ops-content">{children}</main>
      <div className="ops-footer"><span>Himalayan Sentinel <span aria-hidden="true">·</span> Operations</span><span>Evidence first. Human decisions.</span></div>
    </div>
  </div>;
}
