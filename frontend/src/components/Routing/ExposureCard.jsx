import React, { useEffect, useState } from 'react';
import { TriangleAlert } from 'lucide-react';
import { apiRequest } from '../../services/api';

/**
 * Hazard ≠ risk: for each zone, what a modeled failure would threaten —
 * OSM buildings and road meters in the screening runout path, plus the
 * nearest road segment. Numbers from GET /api/runout/exposure, labeled
 * screening approximation, never observed damage.
 */
export default function ExposureCard() {
  const [zones, setZones] = useState(null);

  useEffect(() => {
    let stop = false;
    apiRequest('/runout/exposure')
      .then((b) => { if (!stop) setZones(b.zones || null); })
      .catch(() => { if (!stop) setZones(null); });
    return () => { stop = true; };
  }, []);

  if (!zones) return null;
  const ranked = Object.entries(zones)
    .map(([id, z]) => ({ id, ...z }))
    .sort((a, b) => b.buildings_n - a.buildings_n)
    .slice(0, 4);
  const worst = ranked[0];

  return (
    <div className="bg-mine-card border border-mine-border rounded-2xl overflow-hidden">
      <div className="px-4 py-2.5 bg-mine-darker border-b border-mine-border flex items-center gap-2">
        <TriangleAlert className="w-4 h-4 text-orange-300" />
        <span className="text-xs font-bold text-mine-text">If it fails — who gets hit?</span>
      </div>
      <div className="px-4 py-3">
        <p className="text-[11px] text-mine-text">
          Worst modeled case: <strong>{worst.id}</strong> threatens{' '}
          <strong>~{worst.buildings_n} buildings</strong>
          {worst.nearest_road_seg && (
            <span> · nearest road {worst.nearest_road_seg} ({worst.nearest_road_m}m)</span>
          )}.
        </p>
        <div className="mt-2 space-y-1">
          {ranked.map((z) => (
            <div key={z.id} className="flex items-center justify-between text-[11px] font-mono text-mine-muted">
              <span>{z.id} · {z.length_m}m path</span>
              <span>~{z.buildings_n} bldg · {Object.values(z.road_m || {}).reduce((a, b) => a + b, 0)}m road</span>
            </div>
          ))}
        </div>
        <p className="text-[10px] text-mine-muted mt-2">
          Screening approximation (steepest-descent paths on SRTM, 100m exposure band).
          Building counts cap at 400 fetched per zone — dense towns undercounted.
        </p>
      </div>
    </div>
  );
}
