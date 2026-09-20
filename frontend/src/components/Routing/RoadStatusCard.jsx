import React from 'react';
import { useTalusContext } from '../../context/TalusContext';
import { AlertOctagon, CheckCircle2, AlertTriangle, Navigation, ShieldCheck, ArrowRight } from 'lucide-react';

const STATUS_ICONS = {
  blocked: { icon: AlertOctagon, color: 'text-red-400', bg: 'bg-red-500/15', border: 'border-red-500/30', label: 'BLOCKED' },
  'at-risk': { icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/30', label: 'AT-RISK' },
  open: { icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30', label: 'OPEN' },
};

export default function RoadStatusCard({ compact = false }) {
  const { roads, setIsRouteModalOpen, activeRoutePlan, locationData, t } = useTalusContext();
  const liveRoads = roads || [];

  if (!liveRoads.length) {
    return (
      <div className="bg-white border-2 border-zinc-200 rounded-2xl p-4 text-xs text-zinc-600">
        Road status unavailable — backend offline.
      </div>
    );
  }

  return (
    <div className={`bg-white border-2 border-zinc-200 rounded-2xl shadow-sm space-y-3 ${compact ? 'p-3' : 'p-4 sm:p-5'}`}>
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-amber-500/15 text-amber-700 flex items-center justify-center border border-amber-500/30">
            <AlertTriangle className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-black text-zinc-900 uppercase tracking-wider">
              {t('dashboard.roadStatus')}
            </h3>
            <p className="text-[10px] text-zinc-600">
              {locationData?.label || 'Corridor'} · {liveRoads.length} segments · <span className="font-bold text-emerald-700">LIVE</span>
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsRouteModalOpen(true)}
          aria-label="Open recommended route"
          className="flex items-center gap-1 px-2.5 py-1 bg-zinc-900 hover:bg-black text-white rounded-lg text-[11px] font-bold transition-all shadow-sm focus-visible:ring-2"
        >
          <Navigation className="w-3 h-3" />
          <span>{activeRoutePlan?.origin?.zone_id && activeRoutePlan?.destination?.zone_id ? `${activeRoutePlan.origin.zone_id}→${activeRoutePlan.destination.zone_id} Recommended` : 'Recommended Route'}</span>
        </button>
      </div>

      {/* Segments List */}
      <div className={`grid grid-cols-1 gap-2 ${compact ? '' : 'sm:grid-cols-2'}`}>
        {liveRoads.map((seg) => {
          const meta = STATUS_ICONS[seg.status] || STATUS_ICONS.open;
          const Icon = meta.icon;
          const isR2 = seg.id === 'R2';

          return (
            <div
              key={seg.id}
              className={`rounded-xl border flex items-center justify-between gap-2 transition-all ${compact ? 'p-2' : 'p-2.5'} ${
                seg.status === 'blocked'
                  ? 'bg-red-50 border-red-300'
                  : seg.status === 'at-risk'
                  ? 'bg-amber-50 border-amber-300'
                  : 'bg-emerald-50 border-emerald-200'
              }`}
            >
              <div className="flex items-center gap-2 min-w-0">
                <div className={`w-6 h-6 rounded-md flex items-center justify-center shrink-0 ${meta.bg} ${meta.color}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono font-bold text-xs text-zinc-900">{seg.id}</span>
                    {!compact && <span className="text-[11px] font-semibold text-zinc-900 truncate">{seg.name}</span>}
                  </div>
                  <div className="text-[10px] text-zinc-600">
                    {t('road.adj')} <span className="font-semibold text-zinc-900">{seg.adjacent_slope}</span>
                    {isR2 && <span className="text-amber-700 ml-1 font-bold">{t('road.avoids_r2')}</span>}
                  </div>
                </div>
              </div>

              <span className={`text-[10px] font-mono font-black uppercase px-1.5 py-0.5 rounded shrink-0 border ${meta.bg} ${meta.color} ${meta.border}`}>
                {meta.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* R2 Avoidance Note — recommended route, never guaranteed safe */}
      {!compact && (
      <div className="p-2.5 bg-zinc-50 rounded-xl border border-zinc-200 text-[11px] text-zinc-600 flex items-start gap-2">
        <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-zinc-900">{t('road.avoid_title')} </span>
          <span>
            {t('road.avoid_body')}
          </span>
        </div>
      </div>
      )}
    </div>
  );
}
