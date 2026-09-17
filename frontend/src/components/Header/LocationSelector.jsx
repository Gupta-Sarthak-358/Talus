import React from 'react';
import { useTalusContext } from '../../context/TalusContext';
import { REGION_SUPPORT } from '../../data/locations';
import { MapPin, ChevronDown } from 'lucide-react';

export default function LocationSelector() {
  const { activeLocation, switchLocation, locations, locationData, t } = useTalusContext();

  return (
    <div className="relative flex items-center gap-2">
      <div className="flex items-center gap-1.5 text-mine-muted">
        <MapPin className="w-3.5 h-3.5 text-talus-600" />
        <span className="text-[11px] font-semibold hidden sm:inline">{t('header.corridor')}</span>
      </div>
      <div className="relative">
        <select
          value={activeLocation}
          onChange={(e) => switchLocation(e.target.value)}
          className="appearance-none bg-mine-card border border-mine-border hover:border-talus-500 rounded-lg pl-2.5 pr-7 py-1.5 text-xs font-semibold text-mine-text focus:outline-none focus:border-talus-600 transition-colors"
        >
          {Object.values(locations).map((loc) => {
            const label = t(`location.${loc.id}`) !== `location.${loc.id}` ? t(`location.${loc.id}`) : loc.label;
            const badge = loc.live ? t('common.live_ngen') : t('common.no_data');
            return (
              <option key={loc.id} value={loc.id}>
                {label} ● {badge}
              </option>
            );
          })}
        </select>
        <ChevronDown className="w-3 h-3 text-mine-muted absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
      </div>
      <span className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold border bg-emerald-500/15 text-emerald-700 border-emerald-500/30">
        {locationData?.live ? t('common.live_ngen') : t('common.no_data')}
      </span>
      <span
        title={t(REGION_SUPPORT[activeLocation] === 'validated' ? 'location.validated_note' : 'location.unvalidated_note')}
        className={`hidden md:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold border ${REGION_SUPPORT[activeLocation] === 'validated' ? 'bg-emerald-500/15 text-emerald-700 border-emerald-500/30' : 'bg-amber-500/15 text-amber-800 border-amber-500/30'}`}
      >
        {t(REGION_SUPPORT[activeLocation] === 'validated' ? 'location.validated' : 'location.unvalidated')}
      </span>
    </div>
  );
}
