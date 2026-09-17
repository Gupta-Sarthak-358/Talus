import React, { useEffect, useMemo, useRef, useState } from 'react';
import { History, Play, Pause, AlertTriangle, Info } from 'lucide-react';
import { apiRequest } from '../../services/api';

const BAND_STYLE = {
  'Very Low': 'bg-sky-500/15 text-sky-300 border-sky-500/30',
  Low: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  Moderate: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30',
  High: 'bg-orange-500/15 text-orange-300 border-orange-500/30',
  Critical: 'bg-red-500/15 text-red-300 border-red-500/30',
};

/**
 * Temporal replay: "what would TALUS have known before the disaster?"
 * Daily model state (score, band, inputs-on-that-date, input-delta drivers)
 * scrubbed from window-open to event day, plus the lead-time ledger.
 * Causality is asserted at bundle build (series <= event_date); this card
 * only renders the committed evidence, never recomputes it.
 */
export default function ReplayCard() {
  const [bundle, setBundle] = useState(null);
  const [offline, setOffline] = useState(false);
  const [caseId, setCaseId] = useState(null);
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const timer = useRef(null);

  useEffect(() => {
    apiRequest('/replay/series')
      .then((b) => {
        setBundle(b);
        setCaseId(b.cases[0]?.id || null);
      })
      .catch(() => setOffline(true));
  }, []);

  const active = useMemo(
    () => bundle?.cases.find((c) => c.id === caseId) || null,
    [bundle, caseId]
  );

  useEffect(() => {
    setIdx(0);
    setPlaying(false);
  }, [caseId]);

  useEffect(() => {
    if (!playing || !active) return;
    timer.current = setInterval(() => {
      setIdx((i) => {
        if (i >= active.series.length - 1) {
          setPlaying(false);
          return i;
        }
        return i + 1;
      });
    }, 700);
    return () => clearInterval(timer.current);
  }, [playing, active]);

  if (offline) {
    return (
      <div className="bg-mine-card border border-mine-border rounded-2xl p-6 text-center text-xs text-mine-muted">
        Replay evidence needs the backend (offline). Start it, then open the Lab page.
      </div>
    );
  }
  if (!bundle || !active) {
    return (
      <div className="bg-mine-card border border-mine-border rounded-2xl p-6 text-center text-xs text-mine-muted">
        Loading temporal replay…
      </div>
    );
  }

  const row = active.series[idx];
  const isEventDay = row.date === active.event_date;
  const maxScore = 100;
  const W = 560;
  const H = 120;
  const pts = active.series
    .map((r, i) => `${((i / (active.series.length - 1)) * W).toFixed(1)},${(H - (r.score / maxScore) * (H - 14) - 4).toFixed(1)}`)
    .join(' ');
  const curX = (idx / (active.series.length - 1)) * W;

  return (
    <div className="bg-mine-card border border-mine-border rounded-2xl overflow-hidden">
      <div className="p-4 bg-mine-darker border-b border-mine-border flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-bold text-mine-text">Temporal replay — what did TALUS know, and when?</h3>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {bundle.cases.map((c) => (
            <button
              key={c.id}
              onClick={() => setCaseId(c.id)}
              className={`text-[11px] px-2.5 py-1 rounded-lg border transition-colors ${
                c.id === caseId
                  ? 'bg-sky-500/20 text-sky-200 border-sky-500/40 font-bold'
                  : 'text-mine-muted border-mine-border hover:text-mine-text'
              }`}
            >
              {c.id.split('-')[0]}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 space-y-4">
        <div>
          <h4 className="text-xs font-bold text-mine-text">{active.title}</h4>
          <p className="text-[11px] text-mine-muted mt-0.5">{active.site_name} · event {active.event_date}
            {active.event_date_fuzzy ? ` (${active.event_date_fuzzy})` : ''}</p>
        </div>

        <svg viewBox={`0 0 ${W} ${H}`} className="w-full rounded-xl border border-mine-border bg-mine-darker" role="img"
          aria-label={`Risk trajectory for ${active.title}`}>
          <rect x="0" y="0" width={W} height={H * 0.15} fill="rgba(239,68,68,0.10)" />
          <rect x="0" y={H * 0.15} width={W} height={H * 0.10} fill="rgba(249,115,22,0.10)" />
          <polyline points={pts} fill="none" stroke="#38bdf8" strokeWidth="2" />
          <line x1={W - 1} y1="0" x2={W - 1} y2={H} stroke="#ef4444" strokeWidth="2" strokeDasharray="4 3" />
          <line x1={curX} y1="0" x2={curX} y2={H} stroke="#e2e8f0" strokeWidth="1.5" />
          <circle cx={curX} cy={H - (row.score / maxScore) * (H - 14) - 4} r="4" fill="#e2e8f0" />
        </svg>

        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={() => setPlaying((p) => !p)}
            className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg bg-sky-500/20 text-sky-200 border border-sky-500/40"
          >
            {playing ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            {playing ? 'Pause' : 'Replay'}
          </button>
          <input
            type="range" min={0} max={active.series.length - 1} value={idx}
            onChange={(e) => { setIdx(Number(e.target.value)); setPlaying(false); }}
            className="flex-1 min-w-[180px]" aria-label="Replay date"
          />
          <span className="text-xs font-mono text-mine-text">{row.date}</span>
          <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${BAND_STYLE[row.band]}`}>
            {row.band} · {row.score.toFixed(0)}
          </span>
        </div>

        {isEventDay && (
          <div className="flex items-center gap-2 text-xs font-bold text-red-300 bg-red-500/10 border border-red-500/30 rounded-xl px-3 py-2">
            <AlertTriangle className="w-4 h-4" /> EVENT DAY — {active.event_date}. {active.event_note}
          </div>
        )}

        <div className="border border-mine-border rounded-xl p-3">
          <h5 className="text-[11px] font-bold text-mine-text mb-1.5">Why {row.band} on {row.date}?</h5>
          <ul className="text-[11px] text-mine-muted space-y-0.5">
            {row.drivers.map((d, i) => <li key={i}>· {d}</li>)}
          </ul>
          <p className="text-[11px] font-mono text-mine-muted mt-1.5">
            rain 7d {row.rain_7d.toFixed(0)}mm · 24h {row.rain_24h.toFixed(0)}mm · soil {row.soil_moisture.toFixed(3)} · NDVI {row.ndvi.toFixed(2)}
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="text-left text-mine-muted border-b border-mine-border">
                <th className="py-1 pr-2">event</th>
                <th className="py-1 pr-2">first High</th>
                <th className="py-1 pr-2">lead</th>
                <th className="py-1 pr-2">first Critical</th>
                <th className="py-1">early hot episodes</th>
              </tr>
            </thead>
            <tbody>
              {bundle.ledger.map((L) => (
                <tr key={L.id} className={`border-b border-mine-border/50 ${L.id === caseId ? 'text-mine-text font-bold' : 'text-mine-muted'}`}>
                  <td className="py-1 pr-2">{L.id}</td>
                  <td className="py-1 pr-2 font-mono">{L.first_high || '—'}</td>
                  <td className="py-1 pr-2 font-mono">{L.lead_high_days != null ? `${L.lead_high_days}d` : '—'}</td>
                  <td className="py-1 pr-2 font-mono">{L.first_critical || '—'}</td>
                  <td className="py-1 font-mono">{L.early_hot_episodes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="text-[10px] text-mine-muted flex gap-1.5 items-start">
          <Info className="w-3 h-3 mt-0.5 shrink-0" />
          <span>Causality: every day shows inputs available ON that date only (trailing IMD sums, same/prior-day soil,
            one pre-event satellite scene, static terrain — asserted at bundle build). Analogue row {active.analogue.row}
            ({active.analogue.lulc}, {active.analogue.distance_m}m away). Early hot episodes are prior heat runs, not
            necessarily false — Dipudara's early episode was the precursor swarm that triggered evacuation.</span>
        </p>
      </div>
    </div>
  );
}
