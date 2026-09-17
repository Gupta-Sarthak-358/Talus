import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { FileText, AlertTriangle, Clock, MapPin } from 'lucide-react';

/**
 * Ops wants queue triaged in <10s: flagged first, then queued, newest first.
 * Senior: pure render, no fetch — reports already in context. Max 5 preview.
 */
export default function OpsQueuePreview({ reports, t }) {
  const safe = reports || [];
  const preview = useMemo(() => {
    const flagged = safe.filter((r) => r.status === 'flagged');
    const queued = safe.filter((r) => r.status === 'queued');
    return [...flagged, ...queued].slice(0, 5);
  }, [safe]);

  if (!safe.length) return <div className="text-xs text-mine-muted p-3">No field reports — queue empty. Backend may be offline.</div>;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold text-mine-text flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-talus-600" /> Field Queue — {preview.length}/{reports.length}
        </h3>
        <Link to="/reports" className="text-[11px] font-bold text-talus-600 hover:text-talus-700">Open full queue →</Link>
      </div>
      <div className="space-y-1.5 max-h-[320px] overflow-auto pr-1">
        {preview.map((r) => (
          <div key={r.id} className={`p-2.5 rounded-xl border text-xs ${r.status === 'flagged' ? 'bg-amber-50 border-amber-300' : 'bg-white border-mine-border'}`}>
            <div className="flex items-center gap-1.5">
              <span className="font-mono font-bold text-talus-700">{r.id}</span>
              <span className={`px-1 py-0.5 rounded text-[10px] font-bold uppercase border ${r.status === 'flagged' ? 'bg-amber-500 text-white border-amber-600' : 'bg-zinc-800 text-white border-zinc-900'}`}>{r.status}</span>
              <span className="ml-auto text-[11px] text-mine-muted flex items-center gap-1"><MapPin className="w-3 h-3" /> {r.zone_id}</span>
            </div>
            <p className="mt-1 text-mine-text leading-snug line-clamp-2">“{r.text}”</p>
            <div className="mt-1 flex items-center gap-2 text-[11px] text-mine-muted">
              <Clock className="w-3 h-3" /> {new Date(r.created_at || r.captured_at).toLocaleString()}
              {r.flagged_reason && <span className="text-amber-700 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> {r.flagged_reason.slice(0, 40)}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
