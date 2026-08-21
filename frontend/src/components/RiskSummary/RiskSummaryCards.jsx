import React from 'react';
import { useMineContext } from '../../context/MineContext';
import { AlertTriangle, ShieldAlert, CheckCircle2, Database, Users, TrendingUp } from 'lucide-react';

export default function RiskSummaryCards() {
  const { riskSummary, zones, selectZone, selectedZoneId } = useMineContext();

  if (!riskSummary) return null;

  const criticalZones = zones.filter((z) => z.risk_band === 'CRITICAL');
  const highZones = zones.filter((z) => z.risk_band === 'HIGH');
  const moderateZones = zones.filter((z) => z.risk_band === 'MODERATE');
  const lowZones = zones.filter((z) => z.risk_band === 'LOW' || z.risk_band === 'VERY_LOW');

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {/* Critical & High Risk Zones Card */}
      <div
        onClick={() => {
          if (criticalZones.length > 0) selectZone(criticalZones[0].id);
          else if (highZones.length > 0) selectZone(highZones[0].id);
        }}
        className="cursor-pointer bg-mine-card hover:bg-mine-dark border border-risk-critical/30 hover:border-risk-critical/60 rounded-xl p-3.5 transition-all shadow-sm group relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-24 h-24 bg-risk-critical/5 rounded-full blur-xl group-hover:bg-risk-critical/10 transition-all"></div>
        <div className="flex items-center justify-between">
          <div className="w-8 h-8 rounded-lg bg-risk-critical/15 text-risk-critical flex items-center justify-center">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <span className="text-[11px] font-bold text-risk-critical uppercase tracking-wider px-2 py-0.5 rounded bg-risk-critical/10 border border-risk-critical/20">
            Escalated
          </span>
        </div>
        <div className="mt-2.5 flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-mine-text font-mono">
            {riskSummary.criticalCount + riskSummary.highCount}
          </span>
          <span className="text-xs text-mine-muted font-medium">
            High / Critical Zone{riskSummary.criticalCount + riskSummary.highCount !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-mine-muted border-t border-mine-border pt-1.5">
          <span>Affected: {highZones.map((z) => z.name.split('—')[0]).join(', ') || 'Zone B'}</span>
          <span className="text-risk-critical font-semibold flex items-center gap-0.5">
            <TrendingUp className="w-3 h-3" /> Action req.
          </span>
        </div>
      </div>

      {/* Moderate Risk Card */}
      <div
        onClick={() => {
          if (moderateZones.length > 0) selectZone(moderateZones[0].id);
        }}
        className="cursor-pointer bg-mine-card hover:bg-mine-dark border border-risk-moderate/30 hover:border-risk-moderate/60 rounded-xl p-3.5 transition-all shadow-sm group relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-24 h-24 bg-risk-moderate/5 rounded-full blur-xl group-hover:bg-risk-moderate/10 transition-all"></div>
        <div className="flex items-center justify-between">
          <div className="w-8 h-8 rounded-lg bg-risk-moderate/15 text-risk-moderate flex items-center justify-center">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <span className="text-[11px] font-bold text-risk-moderate uppercase tracking-wider px-2 py-0.5 rounded bg-risk-moderate/10 border border-risk-moderate/20">
            Surveillance
          </span>
        </div>
        <div className="mt-2.5 flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-mine-text font-mono">
            {riskSummary.moderateCount}
          </span>
          <span className="text-xs text-mine-muted font-medium">Moderate Zone (Zone C)</span>
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-mine-muted border-t border-mine-border pt-1.5">
          <span>Central Sump Drainage</span>
          <span className="text-risk-moderate font-medium">Monitoring</span>
        </div>
      </div>

      {/* Stable / Low Risk Card */}
      <div
        onClick={() => {
          if (lowZones.length > 0) selectZone(lowZones[0].id);
        }}
        className="cursor-pointer bg-mine-card hover:bg-mine-dark border border-risk-verylow/30 hover:border-risk-verylow/60 rounded-xl p-3.5 transition-all shadow-sm group relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-24 h-24 bg-risk-verylow/5 rounded-full blur-xl group-hover:bg-risk-verylow/10 transition-all"></div>
        <div className="flex items-center justify-between">
          <div className="w-8 h-8 rounded-lg bg-risk-verylow/15 text-risk-verylow flex items-center justify-center">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <span className="text-[11px] font-bold text-risk-verylow uppercase tracking-wider px-2 py-0.5 rounded bg-risk-verylow/10 border border-risk-verylow/20">
            Nominal
          </span>
        </div>
        <div className="mt-2.5 flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-mine-text font-mono">
            {riskSummary.lowCount}
          </span>
          <span className="text-xs text-mine-muted font-medium">Stable Zones (A, D, E)</span>
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-mine-muted border-t border-mine-border pt-1.5">
          <span>Safe Evacuation Corridors</span>
          <span className="text-risk-verylow font-medium">Clear</span>
        </div>
      </div>

      {/* Data Quality & Telemetry Confidence Card */}
      <div className="bg-mine-card border border-talus-600/30 rounded-xl p-3.5 transition-all shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-24 bg-talus-600/5 rounded-full blur-xl"></div>
        <div className="flex items-center justify-between">
          <div className="w-8 h-8 rounded-lg bg-talus-600/15 text-talus-600 flex items-center justify-center">
            <Database className="w-4 h-4" />
          </div>
          <span className="text-[11px] font-bold text-talus-600 uppercase tracking-wider px-2 py-0.5 rounded bg-talus-600/10 border border-talus-600/20">
            Evidence Quality
          </span>
        </div>
        <div className="mt-2.5 flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-mine-text font-mono">
            {riskSummary.dataQualityConfidence}%
          </span>
          <span className="text-xs text-mine-muted font-medium">Mean Model Confidence</span>
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-mine-muted border-t border-mine-border pt-1.5">
          <span className="truncate">1 Sensor Stale (SEIS-B01)</span>
          <span className="text-risk-moderate font-medium shrink-0">Uncertainty flag</span>
        </div>
      </div>
    </div>
  );
}
