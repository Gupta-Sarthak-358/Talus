import React, { useEffect, useState } from 'react';
import { Shield, Activity, Bell, FileText, Route, MapPin, AlertTriangle } from 'lucide-react';
import { getAuth, clearAuth, DEMO_PINS } from '../services/auth';
import { apiRequest } from '../services/api';
import { useTalusContext } from '../context/TalusContext';

function Section({ title, icon:Icon, children }) {
  return (
    <div className="bg-mine-card border border-mine-border rounded-2xl overflow-hidden">
      <div className="px-4 py-2.5 bg-mine-darker border-b border-mine-border flex items-center gap-2">
        <Icon className="w-4 h-4 text-talus-600" />
        <span className="text-xs font-bold text-mine-text uppercase tracking-wider">{title}</span>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

export default function AdminPage() {
  const { activeLocation, zones, role: ctxRole } = useTalusContext();
  const liveZones = zones || [];
  const [health, setHealth] = useState(null);
  const [healthFailed, setHealthFailed] = useState(false);
  const [db, setDb] = useState(null);
  const [iso, setIso] = useState(null);
  const [log, setLog] = useState([]);
  const [reports, setReports] = useState([]);
  const [calib, setCalib] = useState(null);
  // Reactive gate: context role updates on PIN login even when already on /admin
  // (same-path navigate is a no-op, so a localStorage snapshot alone would stay stale).
  const auth = { ...getAuth(), role: ctxRole || getAuth().role };

  useEffect(() => {
    let stop = false;
    const base = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/api\/?$/, '');
    fetch(`${base}/health`).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); }).then((d) => { if (!stop) { setHealth(d); setHealthFailed(false); } }).catch(() => { if (!stop) setHealthFailed(true); });
    apiRequest(`/isolation?location=${activeLocation}`).then((d) => { if (!stop) setIso(d); }).catch(() => {});
    apiRequest('/alerts/dispatch/log?limit=10').then((d) => { if (!stop) setLog(d.entries || []); }).catch(() => {});
    apiRequest('/reports/queue').then((d) => { if (!stop) setReports(d.reports || []); }).catch(() => {});
    apiRequest('/db/status').then((d) => { if (!stop) setDb(d); }).catch(() => {});
    apiRequest('/model/calib?pi_real=0.01').then((d) => { if (!stop) setCalib(d); }).catch(() => {});
    return () => { stop = true; };
  }, [activeLocation]);

  if (auth.role !== 'admin' && auth.role !== 'state_manager' && auth.role !== 'district_officer') {
    return (
      <main className="max-w-3xl mx-auto px-4 py-10 text-center space-y-3">
        <Shield className="w-10 h-10 text-mine-muted mx-auto" />
        <h2 className="text-lg font-bold text-mine-text">Admin — credentials required</h2>
        <p className="text-sm text-mine-muted">Use PIN 9999 (admin) or officer PINs via the role switcher. This panel shows health, isolation, dispatch log, and provenance not shown to villagers.</p>
      </main>
    );
  }

  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-lg font-extrabold text-mine-text flex items-center gap-2">
          <Shield className="w-5 h-5 text-talus-600" /> Admin Panel
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-mine-darker border border-mine-border text-mine-muted">{auth.role}</span>
        </h1>
        <button onClick={()=>{clearAuth(); location.reload();}} className="text-xs px-3 py-1.5 bg-mine-darker border border-mine-border rounded-lg text-mine-muted hover:text-mine-text">Lock / Switch role</button>
      </div>
      <p className="text-xs text-mine-muted">Villagers see only danger/safe + map. Officers see actions. This panel holds the technical provenance (model, OSM counts, Brier, calibration) that the final product hides from the field. {liveZones.length} slopes live via GET /api/zones.</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Section title="System health" icon={Activity}>
          {healthFailed && !health ? (
            <div className="text-xs text-mine-muted">Health unreachable — backend offline.</div>
          ) : (
          <pre className="text-[11px] font-mono bg-mine-darker border border-mine-border rounded-lg p-3 overflow-auto max-h-56 text-mine-text">
            {health ? JSON.stringify({ ...health, db, calib: calib ? { brier: calib.brier, pi_real: calib.pi_real } : undefined }, null, 2) : 'loading...'}
          </pre>
          )}
        </Section>

        <Section title={`Isolation — ${activeLocation}`} icon={AlertTriangle}>
          {iso ? (
            <div className="space-y-2 text-xs">
              <div className="font-mono">Isolated: {iso.isolated_zones.length ? iso.isolated_zones.join(', ') : 'none'} · May isolate: {iso.at_risk_zones.length ? iso.at_risk_zones.join(', ') : 'none'}</div>
              <div className="text-mine-muted">Bottleneck R1 {iso.bottleneck.R1} · R2 {iso.bottleneck.R2} · R3 {iso.bottleneck.R3} · R4 {iso.bottleneck.R4}</div>
              {iso.action && <div className="bg-amber-950/20 border border-amber-500/20 rounded-lg p-2 text-mine-text">{iso.action}</div>}
              <div className="max-h-40 overflow-auto border border-mine-border rounded-lg divide-y divide-mine-border/50">
                {iso.zones.map(z=>(
                  <div key={z.zone_id} className="px-2.5 py-1.5 flex items-center justify-between gap-2">
                    <span className="font-mono font-bold text-mine-text">{z.zone_id} {z.band} {z.score}</span>
                    <span className={`text-[11px] px-1.5 py-0.5 rounded border ${z.isolated?'bg-red-500/15 text-red-300 border-red-500/30':z.may_isolate?'bg-amber-500/15 text-amber-300 border-amber-500/30':'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'}`}>{z.status}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : 'loading...'}
        </Section>

        <Section title="Dispatch log (SMS/app)" icon={Bell}>
          <div className="text-xs text-mine-muted mb-2">Every alert is logged to runs/alert_dispatch.jsonl with provider status. No fake success.</div>
          <div className="space-y-1 max-h-56 overflow-auto font-mono text-[11px]">
            {log.length ? log.map((e,i)=>(
              <div key={i} className="border border-mine-border rounded p-1.5 bg-mine-darker text-mine-text">
                <div>{e.ts} · {e.channel} · {e.lang} · {e.zone_id} {e.simulated?'SIM':''} {e.sms_ok?'SENT':''}</div>
                <div className="text-mine-muted truncate">{String(e.message||'').slice(0,120)}</div>
              </div>
            )) : <span className="text-mine-muted">no dispatches yet</span>}
          </div>
        </Section>

        <Section title="Field reports queue" icon={FileText}>
          <div className="text-xs text-mine-muted mb-2">{reports.length} reports · queued/flagged/verified</div>
          <div className="space-y-1 max-h-56 overflow-auto text-[11px]">
            {reports.slice(0,10).map(r=>(
              <div key={r.id} className="border border-mine-border rounded p-1.5 bg-mine-darker">
                <div className="font-bold text-mine-text">{r.id} · {r.zone_id} · {r.type} · {r.status}</div>
                <div className="text-mine-muted line-clamp-2">{r.text}</div>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Routing" icon={Route}>
          <p className="text-xs text-mine-muted">Shortest via R2 (blocked/at-risk) vs safe via R3+R4. Isolation engine uses same bottleneck table. Deterministic avoidance, not score-threshold.</p>
        </Section>

        <Section title="Provenance (hidden from field)" icon={MapPin}>
          <div className="text-xs space-y-1 text-mine-muted">
            <div>Model: RF 500 trees + isotonic · 2936 rows (1468+1468) · 17 numeric + lulc · GroupKFold8 RF 0.9345 XGB 0.9421 Brier 0.0967</div>
            <div>Rain: IMD 0.25deg 1901-2024 · Soil: ESA CCI v09.2 1978-2024 · Quakes: USGS 26 M5+ · DEM: SRTM 30m · OSM: Gangtok 1014/Lachung 226/Darjeeling 504</div>
            <div>Wound: Sentinel-2 matched Nov23 vs Nov24 (2 scars, 4/2936) · Runout: SRTM steepest-descent 85 buildings · Panchayat 100 tiles · COP30 S1 28.3→28.7</div>
            <div>Recalibration: pi_train 0.5 → pi_real 0.01 (Bayes) — score frozen, confidence_real_1pct added · SWI JMA 3-tank L1=15</div>
            <div>PINs: {Object.entries(DEMO_PINS).map(([k,v])=>`${k}:${v||'open'}`).join(' · ')}</div>
          </div>
        </Section>
      </div>
    </main>
  );
}
