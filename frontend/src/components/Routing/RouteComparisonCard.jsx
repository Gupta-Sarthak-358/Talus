import React from 'react';
import { useTalusContext } from '../../context/TalusContext';
import { ShieldCheck, AlertOctagon, Clock, Navigation, ArrowRight } from 'lucide-react';

export default function RouteComparisonCard({ routePlan }) {
  const { t } = useTalusContext();
  if (!routePlan) return null;

  const { normalRoute, riskAwareRoute, comparison } = routePlan;

  return (
    <div className="space-y-4">
      {/* Summary Highlight */}
      <div className="p-3 bg-mine-darker border border-mine-border rounded-xl text-xs text-mine-text flex items-start gap-2.5 shadow-sm">
        <ShieldCheck className="w-5 h-5 text-risk-verylow shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-mine-text uppercase tracking-wide">
            {t('route.rec_title')}
          </div>
          <p className="text-[11px] text-mine-muted leading-relaxed">
            {comparison.summary}
          </p>
        </div>
      </div>

      {/* Side-by-Side Comparison Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* 1. Shortest / Normal Route */}
        <div className="p-3.5 bg-mine-darker border border-risk-critical/30 rounded-xl space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-risk-critical bg-risk-critical/15 px-2 py-0.5 rounded border border-risk-critical/30">
              {t('route.shortest')}
            </span>
            <AlertOctagon className="w-4 h-4 text-risk-critical" />
          </div>

          <div>
            <div className="text-sm font-bold text-mine-text">{normalRoute.name}</div>
            <div className="text-[11px] text-risk-critical mt-0.5">
              {t('route.traverses')} {normalRoute.passesThroughHazardZone}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-xs border-t border-mine-border">
            <div>
              <div className="text-[10px] text-mine-muted font-sans">{t('route.distance')}</div>
              <div className="font-bold text-mine-text">{normalRoute.distanceKm} km</div>
            </div>
            <div>
              <div className="text-[10px] text-mine-muted font-sans">{t('route.exposure')}</div>
              <div className="font-bold text-risk-critical">{normalRoute.riskExposureScore} (HIGH)</div>
            </div>
          </div>

          <div className="text-[10px] text-risk-critical italic">
            ⚠ {normalRoute.hazardDescription}
          </div>
        </div>

        {/* 2. Risk-Aware Route */}
        <div className="p-3.5 bg-mine-darker border border-risk-verylow/40 rounded-xl space-y-2.5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-risk-verylow bg-risk-verylow/15 px-2 py-0.5 rounded border border-risk-verylow/30">
              {t('route.safe_title')}
            </span>
            <Navigation className="w-4 h-4 text-risk-verylow" />
          </div>

          <div>
            <div className="text-sm font-bold text-mine-text">{riskAwareRoute.name}</div>
            <div className="text-[11px] text-risk-verylow mt-0.5">
              {t('route.avoids_r2')}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-xs border-t border-mine-border">
            <div>
              <div className="text-[10px] text-mine-muted font-sans">{t('route.distance')}</div>
              <div className="font-bold text-mine-text">{riskAwareRoute.distanceKm} km (+0.3 km)</div>
            </div>
            <div>
              <div className="text-[10px] text-mine-muted font-sans">{t('route.exposure')}</div>
              <div className="font-bold text-risk-verylow">{riskAwareRoute.riskExposureScore} (LOW)</div>
            </div>
          </div>

          <div className="text-[10px] text-risk-verylow">
            ✓ {riskAwareRoute.hazardDescription}
          </div>
        </div>
      </div>
    </div>
  );
}
