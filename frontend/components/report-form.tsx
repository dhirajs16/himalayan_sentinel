"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Region } from "@/lib/types";
export default function ReportForm({ region }: { region: Region }) {
  const [result, setResult] = useState<{ tracking_id: string; status: string } | null>(null);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [mode, setMode] = useState("loading");
  const [coords, setCoords] = useState({ lat: region.lat, lng: region.lng });
  useEffect(() => { setCoords({ lat: region.lat, lng: region.lng }); }, [region]);
  useEffect(() => { api<{ mode: string }>("/reports/verification").then(r => setMode(r.mode)).catch(() => setMode("offline")); }, []);
  async function submit(form: FormData) {
    setBusy(true); setError(""); form.set("region", region.id);
    try { form.set("observed_at", new Date(String(form.get("observed_at"))).toISOString()); setResult(await api("/reports", { method: "POST", body: form })); }
    catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  }
  async function track() {
    if (!result) return;
    try { const update = await api<{ status: string }>(`/reports/${result.tracking_id}`); setResult({ ...result, status: update.status }); } catch (err) { setError((err as Error).message); }
  }
  function gps() {
    if (!navigator.geolocation) { setError("GPS unavailable. Enter coordinates manually."); return; }
    navigator.geolocation.getCurrentPosition(p => setCoords({ lat: p.coords.latitude, lng: p.coords.longitude }), () => setError("Location unavailable. Enter coordinates manually."));
  }
  return <section id="report-incident" className="report card" aria-labelledby="report-title">
    <div className="section-title"><div><span className="eyebrow">Community evidence · private review</span><h3 id="report-title">Report an incident</h3></div></div>
    <p className="muted">Not an emergency dispatch service. Reports remain unverified until human review.</p>
    {error && <p className="error-message" role="alert">{error}</p>}
    {result ? <div className="success" role="status"><b>Observation received · {result.status}</b><p>Save this private tracking code to check your report.</p><code className="tracking-code">{result.tracking_id}</code><button type="button" onClick={track}>Check status</button><button type="button" onClick={() => setResult(null)}>New report</button></div> :
      <form action={submit} className="stack-form">
        <p className="notice">{mode === "demo" ? "Demo verification: no real identity check. Local demonstration only." : "Verification unavailable. Start the local backend to submit a demo report."}</p>
        <label>Region<input value={region.name} readOnly /></label>
        <label>Incident category<select name="category"><option value="sudden_river_rise">Sudden river rise</option><option value="landslide">Landslide</option><option value="blocked_road">Blocked road</option><option value="damaged_bridge">Damaged bridge</option><option value="unusual_water_color">Unusual water color</option><option value="other">Other</option></select></label>
        <label>Description<textarea name="description" required minLength={10} maxLength={2000} placeholder={`What did you observe in ${region.name}?`} /></label>
        <div className="form-row"><label>Latitude<input name="lat" type="number" step="any" min={26} max={31} required value={coords.lat} onChange={e => setCoords({ ...coords, lat: Number(e.target.value) })} /></label><label>Longitude<input name="lng" type="number" step="any" min={80} max={89} required value={coords.lng} onChange={e => setCoords({ ...coords, lng: Number(e.target.value) })} /></label></div>
        <button type="button" className="secondary" onClick={gps}>Use GPS location</button>
        <label>Observation time (your device timezone)<input name="observed_at" type="datetime-local" required /></label>
        <label>Evidence image · JPEG, PNG or WebP · up to 5 MB<input name="image" type="file" accept="image/jpeg,image/png,image/webp" required /></label>
        <label>Contact (optional, private)<input name="contact" maxLength={200} autoComplete="off" /></label>
        <label className="check"><input name="consent" type="checkbox" value="true" required />I consent to private storage and authorized review.</label>
        <label className="check"><input name="accuracy" type="checkbox" value="true" required />This describes my observation accurately.</label>
        <label className="check"><input name="demo_verified" type="checkbox" value="true" required />I understand this is a demo verification mock.</label>
        <button className="primary" disabled={busy || mode !== "demo"}>{busy ? "Uploading evidence…" : "Submit for review"}</button>
      </form>}
  </section>;
}
