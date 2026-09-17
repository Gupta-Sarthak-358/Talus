import React from 'react';
import { CheckCircle2, AlertTriangle, XOctagon, MapPin } from 'lucide-react';

/**
 * Villager: plain-language road cards, no R-codes jargon, high contrast, 48px tap.
 * Senior: memoized, no fetch here — roads passed from context.
 */
const PlainStatus = {
  blocked: { icon: XOctagon, key: 'closed', cls: 'bg-red-600 text-white border-red-700' },
  'at-risk': { icon: AlertTriangle, key: 'risky', cls: 'bg-amber-400 text-zinc-900 border-amber-500' },
  open: { icon: CheckCircle2, key: 'open_simple', cls: 'bg-emerald-600 text-white border-emerald-700' },
};

export default function VillagerRoadPlain({ roads = [], t }) {
  if (!roads.length) return null;
  return (
    <div className="bg-white border-2 border-zinc-200 rounded-2xl p-4 space-y-3">
      <h2 className="text-sm font-extrabold text-zinc-900 flex items-center gap-2">
        <MapPin className="w-4 h-4 text-zinc-700" /> {t('villager.road_status') || 'Road Status — Simple'}
      </h2>
      <div className="grid gap-2">
        {roads.map((r) => {
          const meta = PlainStatus[r.status] || PlainStatus.open;
          const Icon = meta.icon;
          return (
            <div key={r.id} className={`flex items-center gap-3 p-3 rounded-xl border-2 ${meta.cls}`}>
              <Icon className="w-6 h-6 shrink-0" aria-hidden />
              <div className="min-w-0 flex-1">
                <div className="font-bold text-sm leading-tight">{r.name?.replace('Ridge shortcut S1-S4', 'Hillside shortcut')}</div>
                <div className="text-xs opacity-90">{r.description?.split('—')[0]?.slice(0, 60)}</div>
              </div>
              <div className="text-right">
                <div className="font-black text-xs tracking-widest">{t(`road.status.${meta.key}`)}</div>
                <div className="text-[11px] font-semibold">{t(`road.sub.${meta.key}`)}</div>
              </div>
            </div>
          );
        })}
      </div>
      <p className="text-[11px] text-zinc-600 text-center">{t('villager.road_hint') || 'Green = go, Yellow = caution, Red = do not go.'}</p>
    </div>
  );
}
