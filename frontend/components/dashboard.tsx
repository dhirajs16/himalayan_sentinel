"use client";
import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CloudRain,
  MapPin,
  Radio,
  Telescope,
  Users,
  Waves,
  Wind,
} from "lucide-react";
import Charts from "./charts";
import Link from "next/link";
import LakeMonitor, { PublicAlerts } from "./lake-monitor";
import ReportForm from "./report-form";
import EvidenceExplorer from "./evidence-explorer";
import { fallbackRegions } from "@/lib/data";
import type { Region, RiskLevel } from "@/lib/types";
const RiskMap = dynamic(() => import("./risk-map"), {
  ssr: false,
  loading: () => <div className="map loading">Loading map…</div>,
});
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const pill: Record<RiskLevel, string> = {
  Low: "low",
  Moderate: "moderate",
  High: "high",
  Critical: "critical",
};
export default function Dashboard() {
  const [regions, setRegions] = useState(fallbackRegions);
  const [selected, setSelected] = useState<Region>(fallbackRegions[0]);
  const [language, setLanguage] = useState<"en" | "ne">("en");
  const [alert, setAlert] = useState<{
    sms: string;
    checklist: string[];
  } | null>(null);
  const [generating, setGenerating] = useState(false);
  const [offline, setOffline] = useState(false);
  const [query, setQuery] = useState("");
  useEffect(() => {
    fetch(`${API}/regions`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data: Region[]) => {
        setRegions(data);
        setSelected(data[0]);
      })
      .catch(() => { setOffline(true); });
  }, []);
  const stats = useMemo(
    () => ({
      critical: regions.filter((r) => r.risk.level === "Critical").length,
      reports: regions.reduce((a, r) => a + r.reports, 0),
      rain: Math.round(
        regions.reduce((a, r) => a + r.rainfall_mm, 0) / regions.length,
      ),
      highest: [...regions].sort((a, b) => b.risk.score - a.risk.score)[0],
    }),
    [regions],
  );
  async function generate() {
    setGenerating(true);
    try {
      const res = await fetch(`${API}/ai/generate-alert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ region_id: selected.id, language }),
      });
      if (!res.ok) throw new Error();
      setAlert(await res.json());
    } catch {
      setAlert({
        sms:
          language === "ne"
            ? `सतर्कता: ${selected.name} मा ${selected.risk.level} जोखिम। नदी किनारबाट टाढा रहनुहोस् र आधिकारिक सूचना सुन्नुहोस्।`
            : `ADVISORY: ${selected.risk.level} flood-risk estimate for ${selected.name}. Stay away from riverbanks and follow official updates. Not an official warning.`,
        checklist:
          language === "ne"
            ? [
                "फोन चार्ज गर्नुहोस्",
                "पानी र औषधि तयार राख्नुहोस्",
                "सुरक्षित मार्ग तय गर्नुहोस्",
              ]
            : [
                "Charge phones and power banks",
                "Pack water and essential medicine",
                "Agree on a safe route",
              ],
      });
    } finally {
      setGenerating(false);
    }
  }
  const explanation =
    language === "ne"
      ? `${selected.name} मा जोखिम स्तर ${selected.risk.level} (${selected.risk.score}/100) छ। वर्षा, नदीको अवस्था र हिमतालसम्बन्धी जोखिम मुख्य कारण हुन्। यो आधिकारिक विपद् चेतावनी होइन।`
      : `${selected.name} is rated ${selected.risk.level} (${selected.risk.score}/100). Recent rainfall, a ${selected.river_status.toLowerCase()} river condition, and ${selected.glacial_risk.toLowerCase()} glacial context are the main drivers.`;
  return (
    <main>
      <header>
        <div className="brand">
          <div className="brandmark">
            <Telescope size={22} />
          </div>
          <div>
            <b>HIMALAYAN SENTINEL</b>
            <span>Nepal risk intelligence</span>
          </div>
        </div>
        <div className="status">
          <i /> Monitoring active <span>•</span> Seeded demo
        </div>
        <nav className="header-actions" aria-label="Main"><a href="#report-incident" className="primary">Report an incident</a><Link href="/operations">Staff sign in</Link></nav>
      </header>
      <div className="shell">
        <p className="notice" role="status">Decision-support system · prototype weights and simulated regional indicators. {offline ? "API offline: regional fixtures shown. Reports cannot be submitted offline." : "Regional cards below use demo data; lake inventory and published alerts are separate."} Always follow official government instructions.</p>
        <PublicAlerts language={language} />
        <section className="intro">
          <div>
            <span className="eyebrow accent">Decision support · Nepal</span>
            <h1>
              See the signals.
              <br />
              <em>Act earlier.</em>
            </h1>
            <p>
              One calm, explainable view of flood and glacial-lake risk
              signals—built for communities and local responders.
            </p>
          </div>
          <div className="timestamp">
            <Radio size={16} /> Regional fixture timestamp
            <br />
            <strong>10 Oct 2026 · 14:30 NPT</strong>
          </div>
        </section>
        <section className="stats">
          <Stat
            icon={<AlertTriangle />}
            label="Critical demo regions"
            value={String(stats.critical)}
            note="of 8 monitored"
            tone="red"
          />
          <Stat
            icon={<Users />}
            label="Community reports"
            value={String(stats.reports)}
            note="seeded today"
          />
          <Stat
            icon={<CloudRain />}
            label="Average rainfall"
            value={`${stats.rain} mm`}
            note="latest 24h signal"
          />
          <Stat
            icon={<Waves />}
            label="Highest demo priority"
            value={stats.highest.basin.split("–")[0]}
            note={`${stats.highest.risk.score} risk score`}
          />
        </section>
        <EvidenceExplorer />
        <LakeMonitor />
        <label className="region-search">Search monitored demo districts or basins<input value={query} onChange={e => setQuery(e.target.value)} placeholder="Rasuwa, Koshi…" /></label>
        <div className="region-options">{regions.filter(r => `${r.name} ${r.province} ${r.basin}`.toLowerCase().includes(query.toLowerCase())).map(r => <button key={r.id} className={selected.id === r.id ? "active" : ""} onClick={() => { setSelected(r); setAlert(null); }}>{r.name}</button>)}</div>
        <section className="workspace">
          <div className="map-card card">
            <div className="section-title overlay">
              <div>
                <span className="eyebrow">Situation map</span>
                <h2>Simulated regional indicators</h2>
              </div>
              <div className="legend">
                <i className="low" />
                Low <i className="moderate" />
                Moderate <i className="high" />
                High <i className="critical" />
                Critical
              </div>
            </div>
            <RiskMap
              regions={regions}
              selected={selected.id}
              onSelect={(r) => {
                setSelected(r);
                setAlert(null);
              }}
            />
          </div>
          <aside className="detail card">
            <div className="detail-top">
              <div>
                <span className="eyebrow">Selected region</span>
                <h2>{selected.name}</h2>
                <p>
                  <MapPin size={14} />
                  {selected.province} · {selected.basin}
                </p>
              </div>
              <span className={`risk-pill ${pill[selected.risk.level]}`}>
                {selected.risk.level}
              </span>
            </div>
            <div className="score">
              <div>
                <strong>{selected.risk.score}</strong>
                <span>/100</span>
              </div>
              <div className="meter">
                <i style={{ width: `${selected.risk.score}%` }} />
              </div>
              <small>Demo monitoring score · legacy regional rules</small>
            </div>
            <div className="metrics">
              <Metric
                label="24h rainfall"
                value={`${selected.rainfall_mm} mm`}
                icon={<CloudRain />}
              />
              <Metric
                label="River status"
                value={selected.river_status}
                icon={<Waves />}
              />
              <Metric
                label="Glacial context"
                value={selected.glacial_risk}
                icon={<Wind />}
              />
              <Metric
                label="Simulated exposure"
                value={selected.population_exposed.toLocaleString()}
                icon={<Users />}
              />
            </div>
            <div className="explain">
              <div className="ai-label">✦ AI-assisted explanation</div>
              <p>{explanation}</p>
              <small>
                This is a decision-support estimate, not an official disaster
                warning.
              </small>
            </div>
            <div className="actions">
              <div className="segmented">
                <button
                  onClick={() => setLanguage("en")}
                  className={language === "en" ? "active" : ""}
                >
                  English
                </button>
                <button
                  onClick={() => setLanguage("ne")}
                  className={language === "ne" ? "active" : ""}
                >
                  नेपाली
                </button>
              </div>
              <button
                className="primary"
                onClick={generate}
                disabled={generating}
              >
                {generating ? "Generating…" : "Prepare safety advisory"}
              </button>
            </div>
            {alert && (
              <div className="alert-output">
                <b>Demo safety advisory · not an official alert</b>
                <p>{alert.sms}</p>
                <ul>
                  {alert.checklist.map((x) => (
                    <li key={x}>{x}</li>
                  ))}
                </ul>
              </div>
            )}
          </aside>
        </section>
        <section className="card panel"><h2>{language === "ne" ? "सुरक्षा मार्गदर्शन" : "Safety guidance and emergency resources"}</h2><p>{language === "ne" ? "आधिकारिक निर्देशन पालना गर्नुहोस्। नदी किनार र क्षतिग्रस्त पुलबाट टाढा रहनुहोस्।" : "Follow local authority notices. Avoid fast-flowing water and damaged bridges. Keep essential medicine, drinking water and a family communication plan ready."}</p><p>No verified shelter or emergency-resource inventory is configured. Contact your municipality for authorized locations and routes.</p></section>
        <section className="lower">
          <Charts region={selected} />
          <ReportForm region={selected} />
        </section>
        <section className="method">
          <div>
            <span className="eyebrow">Transparent by design</span>
            <h2>How the score is calculated</h2>
          </div>
          <div className="formula">
            Rainfall <b>30%</b>
            <span>+</span> River level <b>25%</b>
            <span>+</span> Glacial context <b>20%</b>
            <span>+</span> Community reports <b>15%</b>
            <span>+</span> Exposure <b>10%</b>
          </div>
        </section>
        <footer>
          <div className="brand">
            <div className="brandmark">
              <Telescope size={18} />
            </div>
            <b>HIMALAYAN SENTINEL</b>
          </div>
          <p>
            Prototype for risk awareness only. Always follow Nepal’s official
            disaster authorities.
          </p>
        </footer>
      </div>
    </main>
  );
}
function Stat({
  icon,
  label,
  value,
  note,
  tone = "",
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  note: string;
  tone?: string;
}) {
  return (
    <div className={`stat card ${tone}`}>
      <div className="stat-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{note}</small>
      </div>
    </div>
  );
}
function Metric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="metric">
      <div>{icon}</div>
      <span>
        {label}
        <strong>{value}</strong>
      </span>
    </div>
  );
}
