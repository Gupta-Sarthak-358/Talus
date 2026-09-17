import React from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle } from 'lucide-react';

/**
 * Senior-dev: pure presentational, no fetch. Villager: binary safe/danger only.
 * Ops/mgmt: never render this — they need scores. Villager never sees % or SHAP.
 */
export default function VillagerHero({ zone, t }) {
  const band = zone?.risk_band || '—';
  const isDanger = band === 'CRITICAL' || band === 'HIGH';
  const isCaution = band === 'MODERATE';

  const action = zone?.role_actions?.villager || zone?.role_actions?.['villager'];
  const msg = action?.action || action?.message || (isDanger ? t('villager.avoid_msg') : isCaution ? t('villager.caution') : t('villager.no_restriction'));

  return (
    <div
      role="status"
      aria-live="polite"
      className={`rounded-2xl border-2 p-5 sm:p-6 text-center space-y-3 shadow-sm ${
        isDanger
          ? 'bg-red-600 border-red-700 text-white'
          : isCaution
          ? 'bg-amber-400 border-amber-500 text-zinc-900'
          : 'bg-emerald-600 border-emerald-700 text-white'
      }`}
    >
      <div className="flex items-center justify-center gap-2">
        {isDanger ? <ShieldAlert className="w-7 h-7" aria-hidden /> : isCaution ? <AlertTriangle className="w-7 h-7" aria-hidden /> : <ShieldCheck className="w-7 h-7" aria-hidden />}
        <h1 className="villager-hero">
          {isDanger ? (t('villager.danger') || 'DANGER — Avoid Road') : isCaution ? (t('villager.caution_title') || 'BE CAREFUL') : (t('villager.safe') || 'SAFE')}
        </h1>
        <span className={`px-2 py-1 rounded text-xs font-black tracking-widest ${isDanger ? 'bg-white text-red-700' : isCaution ? 'bg-zinc-900 text-amber-300' : 'bg-white text-emerald-700'}`}>
          {t(`risk.band.${band.toLowerCase()}`) !== `risk.band.${band.toLowerCase()}` ? t(`risk.band.${band.toLowerCase()}`) : band}
        </span>
      </div>
      <p className="villager-tap max-w-2xl mx-auto leading-snug">
        {zone?.name ? `${zone.name}: ` : ''}
        {msg}
      </p>
      {isDanger && <p className="text-sm font-semibold opacity-90">{t('villager.use_valley') || 'Use valley road. Do not use hillside road.'}</p>}
    </div>
  );
}
