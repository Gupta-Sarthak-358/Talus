import React from 'react';
import { useTalusContext } from '../../context/TalusContext';
import { AlertOctagon, CheckCircle2, AlertTriangle, Navigation, ShieldCheck, ArrowRight } from 'lucide-react';

const STATUS_ICONS = {
  blocked: { icon: AlertOctagon, color: 'text-red-400', bg: 'bg-red-500/15', border: 'border-red-500/30', label: 'BLOCKED' },
  'at-risk': { icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/30', label: 'AT-RISK' },
  open: { icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30', label: 'OPEN' },
};

export default function RoadStatusCard() {
  const { roads, setIsRouteModalOpen, activeRoutePlan, locationData, t } = useTalusContext();

  return (
    <div className="bg-mine-card border border-mine-border rounded-2xl p-4 sm:p-5 shadow-sm space-y-3.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-risk-moderate/15 text-risk-moderate flex items-center justify-center border border-risk-moderate/30">
            <AlertTriangle className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-mine-text uppercase tracking-wider">
              {t('dashboard.roadStatus')}
            </h3>
            <p className="text-[10px] text-mine-muted font-mono">
              GET /api/roads/status · {locationData?.label || 'Corridor'} Arterial Graph
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsRouteModalOpen(true)}
          className="flex items-center gap-1 px-2.5 py-1 bg-talus-600 hover:bg-talus-500 text-white rounded-lg text-[11px] font-bold transition-all shadow-sm"
        >
          <Navigation className="w-3 h-3" />
          <span>{activeRoutePlan?.origin?.zone_id && activeRoutePlan?.destination?.zone_id ? `${activeRoutePlan.origin.zone_id}→${activeRoutePlan.destination.zone_id} Safe Route` : 'Safe Route'}</span>
        </button>
      </div>

      {/* Segments List */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {roads.map((seg) => {
          const meta = STATUS_ICONS[seg.status] || STATUS_ICONS.open;
          const Icon = meta.icon;
          const isR2 = seg.id === 'R2';

          return (
            <div
              key={seg.id}
              className={`p-2.5 rounded-xl border flex items-center justify-between gap-2 transition-all ${
                seg.status === 'blocked'
                  ? 'bg-red-950/20 border-red-500/40'
                  : seg.status === 'at-risk'
                  ? 'bg-amber-950/20 border-amber-500/40'
                  : 'bg-mine-darker border-mine-border'
              }`}
            >
              <div className="flex items-center gap-2 min-w-0">
                <div className={`w-6 h-6 rounded-md flex items-center justify-center shrink-0 ${meta.bg} ${meta.color}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono font-bold text-xs text-mine-text">{seg.id}</span>
                    <span className="text-[11px] font-semibold text-mine-text truncate">{seg.name}</span>
                  </div>
                  <div className="text-[10px] text-mine-muted">
                    {t('road.adj')} <span className="font-semibold text-mine-text">{seg.adjacent_slope}</span>
                    {isR2 && <span className="text-amber-400 ml-1 font-bold">{t('road.avoids_r2')}</span>}
                  </div>
                </div>
              </div>

              <span className={`text-[9px] font-mono font-bold uppercase px-1.5 py-0.5 rounded shrink-0 border ${meta.bg} ${meta.color} ${meta.border}`}>
                {meta.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* R2 Avoidance Note */}
      <div className="p-2.5 bg-mine-darker rounded-xl border border-mine-border text-[11px] text-mine-muted flex items-start gap-2">
        <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-mine-text">{t('road.avoid_title')} </span>
          <span>
            {t('road.avoid_body')}
          </span>
        </div>
      </div>
    </div>
  );
}
