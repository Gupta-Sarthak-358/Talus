import React, { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTalusContext } from '../context/TalusContext';
import RiskMap from '../components/RiskMap/RiskMap';
import ZoneIntelligencePanel from '../components/ZoneDetails/ZoneIntelligencePanel';
import { ErrorState } from '../components/Common/LoadingSkeleton';

/**
 * Live-only map — generic GIS + intel, no district chrome.
 * /map shows RiskMap (API geometry primary) + ZoneIntelligencePanel (intel only).
 * Never renders VillagerHero, OpsQueuePreview, road restriction catalogue, or Admin provenance.
 * /role/district_officer is the ops console (sticky warning/isolation + intel/queue/road tabs).
 */
export default function MapPage() {
  const { error, refreshData, selectZone, setLang, zones, scoringMode, locationData } = useTalusContext();
  const liveZones = zones || [];
  const [params] = useSearchParams();

  useEffect(() => {
    const zone = params.get('zone');
    const lang = params.get('lang');
    if (lang) setLang(lang);
    if (zone) selectZone(zone);
  }, [params]);

  if (error) {
    return <div className="max-w-xl mx-auto my-20 p-4"><ErrorState message={error} onRetry={refreshData} /></div>;
  }

  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <div className="bg-zinc-900 text-white rounded-xl px-4 py-2.5 flex flex-wrap items-center justify-between gap-2 text-xs">
        <span className="font-black tracking-wide">Live Map — {(locationData?.label || 'Corridor')} · NGEN</span>
        <span className="text-zinc-300 font-mono">{liveZones.length} slopes · {scoringMode === 'live-rf' ? 'LIVE RF' : 'Fixture fallback'} · API geometry</span>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        <div className="lg:col-span-7 xl:col-span-7 h-[640px] xl:h-[720px] lg:sticky lg:top-[88px] border-2 border-zinc-200 rounded-2xl overflow-hidden order-2 lg:order-1">
          <RiskMap />
        </div>
        <div className="lg:col-span-5 xl:col-span-5 space-y-4 order-1 lg:order-2">
          <ZoneIntelligencePanel />
        </div>
      </div>
    </main>
  );
}
