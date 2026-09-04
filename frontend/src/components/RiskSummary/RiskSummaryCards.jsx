import React from 'react';
import { useTalusContext } from '../../context/TalusContext';
import { AlertTriangle, ShieldAlert, CheckCircle2, Database, TrendingUp, Brain, FlaskConical } from 'lucide-react';

const idsOf = (zones) => zones.map((z) => z.id).join(', ') || '—';

export default function RiskSummaryCards() {
  const { riskSummary, zones, selectZone, selectedZoneId } = useTalusContext();

  if (!riskSummary) return null;

  const criticalZones = zones.filter((z) => z.risk_band === 'CRITICAL');
  const highZones = zones.filter((z) => z.risk_band === 'HIGH');
  const moderateZones = zones.filter((z) => z.risk_band === 'MODERATE');
  const lowZones = zones.filter((z) => z.risk_band === 'LOW' || z.risk_band === 'VERY_LOW');

  return (
    <>
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
            High / Critical Slope{riskSummary.criticalCount + riskSummary.highCount !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-mine-muted border-t border-mine-border pt-1.5 gap-1">
          <span className="truncate">Slopes: {idsOf([...criticalZones, ...highZones])}</span>
          <span className="text-risk-critical font-semibold flex items-center gap-0.5 shrink-0">
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
          <span className="text-xs text-mine-muted font-medium">
            Moderate Slope{riskSummary.moderateCount !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-mine-muted border-t border-mine-border pt-1.5 gap-1">
          <span className="truncate">Slopes: {idsOf(moderateZones)}</span>
          <span className="text-risk-moderate font-medium shrink-0">Monitoring</span>
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
          <span className="text-xs text-mine-muted font-medium">
            Stable Slope{riskSummary.lowCount !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-mine-muted border-t border-mine-border pt-1.5 gap-1">
          <span className="truncate">Slopes: {idsOf(lowZones)}</span>
          <span className="text-risk-verylow font-medium shrink-0">No escalation</span>
        </div>
      </div>

      {/* Data Quality & Model Confidence Card */}
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
          <span className="text-xs text-mine-muted font-medium">Mean Calibrated Confidence</span>
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-mine-muted border-t border-mine-border pt-1.5 gap-1">
          <span className="truncate">Sources: IMD, SRTM, CCI, WorldCover, Bhusanket</span>
          <span className="text-talus-600 font-medium shrink-0">16/17 REAL/PROXY</span>
        </div>
      </div>
    </div>
    {/* Training Phase-1 Badge — LIVE from ml/sih26001/reports/metrics.md */}
    <div className="mt-3 bg-mine-card border border-emerald-500/20 rounded-xl p-3.5 shadow-sm relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-xl"></div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/15 text-emerald-500 flex items-center justify-center border border-emerald-500/20">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-bold text-mine-text flex items-center gap-2">
              Training Phase-1 — Inventory-Scale Susceptibility
              <span className="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-500 border border-emerald-500/20 text-[10px] font-bold uppercase">Live</span>
              <span className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-mine-darker border border-mine-border text-[10px] font-mono text-mine-muted">
                <FlaskConical className="w-3 h-3" /> 1528×22 (764+764)
              </span>
            </div>
            <div className="text-[11px] text-mine-muted font-mono mt-0.5">
              <span className="text-mine-text font-semibold">RF 0.921</span> <span className="text-mine-muted">·</span> <span className="text-mine-text font-semibold">XGB 0.9256</span> <span className="text-mine-muted">·</span> <span className="text-mine-text font-semibold">LGBM 0.9207</span> <span className="text-mine-muted">·</span> <span>Brier 0.1019</span> <span className="text-mine-muted">vs naive 0.25</span> <span className="text-mine-muted">·</span> <span>SHAP 5-pt</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 text-[11px]">
          <span className="px-2 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 font-mono font-bold">
            Temporal 35/73 → RF test 0.9264
          </span>
          <span className="hidden sm:inline text-mine-muted">GroupKFold(8) spatial · 16/17 REAL/PROXY</span>
        </div>
      </div>
      <div className="mt-2.5 flex flex-wrap items-center gap-1.5 text-[10px] font-mono text-mine-muted border-t border-mine-border pt-2.5">
        <span className="px-1.5 py-0.5 rounded bg-mine-darker border border-mine-border">USGS n27_e088</span>
        <span className="px-1.5 py-0.5 rounded bg-mine-darker border border-mine-border">IMD 1991-2020 climatology</span>
        <span className="px-1.5 py-0.5 rounded bg-mine-darker border border-mine-border">CCI 0.271</span>
        <span className="px-1.5 py-0.5 rounded bg-mine-darker border border-mine-border">WorldCover N27E087</span>
        <span className="px-1.5 py-0.5 rounded bg-mine-darker border border-mine-border">Overpass 6698/1320</span>
        <span className="ml-auto text-talus-600 font-medium">ml/sih26001/reports/metrics.md</span>
      </div>
    </div>
    </>
  );
}