import React, { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTalusContext } from '../context/TalusContext';
import RiskMap from '../components/RiskMap/RiskMap';
import ZoneIntelligencePanel from '../components/ZoneDetails/ZoneIntelligencePanel';
import { ErrorState } from '../components/Common/LoadingSkeleton';

export default function MapPage() {
  const { error, refreshData, selectZone, setLang } = useTalusContext();
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
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        <div className="lg:col-span-7 xl:col-span-7 h-[640px] xl:h-[720px] sticky top-[88px]">
          <RiskMap />
        </div>
        <div className="lg:col-span-5 xl:col-span-5 space-y-4">
          <ZoneIntelligencePanel />
        </div>
      </div>
    </main>
  );
}
