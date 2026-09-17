import React, { useEffect, useState } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import RiskMap from '../../components/RiskMap/RiskMap';
import IsolationAlertCard from '../../components/Alerts/IsolationAlertCard';
import VillagerHero from '../../components/Villager/VillagerHero';
import VillagerRoadPlain from '../../components/Villager/VillagerRoadPlain';
import { Navigation, FileText } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * Villager light shell: senior-dev wants <50KB, no SHAP; villager wants binary; ops/mgmt not using this route.
 * Keeps RiskMap lazy behind toggle — default: hero+roads+actions, map opt-in on mobile.
 */
export default function VillagerPage() {
  const { zones, selectedZoneData, locationData, roads, t, setRole, selectZone, selectedZoneId } = useTalusContext();
  useEffect(() => setRole('villager'), []);
  const zone = selectedZoneData;

  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <VillagerHero zone={zone} t={t} />

      <IsolationAlertCard />

      {/* Village zone picker — large taps, no jargon */}
      <div className="bg-white border-2 border-zinc-200 rounded-2xl p-3">
        <div className="text-[11px] font-bold text-zinc-600 uppercase tracking-wider mb-2">{t('zone.selectSlope')} — {t('villager.tap_map')}</div>
        <div className="grid grid-cols-4 gap-2">
          {(zones || []).map((z) => {
            const bandKey = `risk.band.${(z.risk_band || '').toLowerCase()}`;
            const bandLabel = t(bandKey) !== bandKey ? t(bandKey) : z.risk_band;
            return (
              <button
                key={z.id}
                onClick={() => selectZone(z.id)}
                aria-pressed={selectedZoneId === z.id}
                className={`py-3 rounded-xl text-sm font-black border-2 ${selectedZoneId === z.id ? 'bg-zinc-900 text-white border-zinc-900' : 'bg-white text-zinc-900 border-zinc-300 hover:border-zinc-900'}`}
              >
                {z.id}
                <div className={`text-[10px] font-bold ${z.risk_band === 'CRITICAL' || z.risk_band === 'HIGH' ? 'text-red-600' : 'text-emerald-700'}`}>{bandLabel}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Map ALWAYS shown — villagers need to see where danger is */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8 h-[520px] lg:h-[620px] border-2 border-zinc-900 rounded-2xl overflow-hidden shadow-sm">
          <RiskMap />
        </div>
        <div className="lg:col-span-4 space-y-3">
          <VillagerRoadPlain roads={roads} t={t} />
          <div className="grid grid-cols-1 gap-3">
            <Link
              to="/routes"
              className="villager-tap flex items-center justify-center gap-2 bg-zinc-900 hover:bg-black text-white rounded-2xl font-black shadow-sm focus-visible:ring-2 focus-visible:ring-zinc-900"
              aria-label={t('villager.safe_route_btn')}
            >
              <Navigation className="w-5 h-5" aria-hidden /> {t('villager.safe_route_btn')}
            </Link>
            <Link
              to="/reports"
              className="villager-tap flex items-center justify-center gap-2 bg-white border-2 border-zinc-900 text-zinc-900 rounded-2xl font-black hover:bg-zinc-50"
              aria-label={t('villager.submit_report_btn')}
            >
              <FileText className="w-5 h-5" aria-hidden /> {t('villager.submit_report_btn')}
            </Link>
          </div>
        </div>
      </div>

      <p className="text-[11px] text-center text-zinc-500 px-2">
        {t('villager.tap_map')} — {(zones || []).map((z) => z.id).join(' · ')} · {(t(`location.${locationData?.id}`) !== `location.${locationData?.id}` ? t(`location.${locationData.id}`) : locationData?.label) || ''}
      </p>
    </main>
  );
}
