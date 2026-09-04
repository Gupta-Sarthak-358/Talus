import React from 'react';
import { useTalusContext } from '../../context/TalusContext';
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
          {Object.values(locations).map((loc) => (
            <option key={loc.id} value={loc.id}>
              {loc.label} {loc.live ? `● ${t('location.live')}` : `○ ${t('location.preview')}`}
            </option>
          ))}
        </select>
        <ChevronDown className="w-3 h-3 text-mine-muted absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
      </div>
      <span className={`hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold border ${locationData.live ? 'bg-emerald-500/15 text-emerald-700 border-emerald-500/30' : 'bg-amber-500/15 text-amber-700 border-amber-500/30'}`}>
        {locationData.badge}
      </span>
    </div>
  );
}
