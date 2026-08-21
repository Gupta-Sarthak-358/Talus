import React from 'react';
import { useMineContext } from '../../context/MineContext';
import RiskScoreGauge from './RiskScoreGauge';
import ShapChart from './ShapChart';
import RiskTrendChart from './RiskTrendChart';
import MissingEvidenceCard from './MissingEvidenceCard';
import RoleActionCard from './RoleActionCard';
import { LoadingSkeleton } from '../Common/LoadingSkeleton';
import { MapPin, Sliders, ChevronRight, Activity, Zap } from 'lucide-react';

export default function ZoneIntelligencePanel() {
  const {
    zones,
    selectedZoneId,
    selectedZoneData,
    selectZone,
    zoneLoading,
    activeSimulation,
  } = useMineContext();

  if (!selectedZoneData && zoneLoading) {
    return (
      <div className="bg-mine-card border border-mine-border rounded-2xl p-5 shadow-sm space-y-4">
        <LoadingSkeleton lines={8} />
      </div>
    );
  }

  if (!selectedZoneData) {
    return (
      <div className="bg-mine-card border border-mine-border rounded-2xl p-6 text-center text-mine-muted">
        Select a mine zone on the map or choose below to inspect risk intelligence.
      </div>
    );
  }

  const zone = selectedZoneData;

  return (
    <div className="bg-mine-card border border-mine-border rounded-2xl p-4 sm:p-5 shadow-sm space-y-4">
      {/* Zone Selector Pills */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-[11px] font-semibold text-mine-muted uppercase tracking-wider">
          <span className="flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-talus-600" />
            <span>Select Pit Sector</span>
          </span>
          <span className="text-[10px] text-mine-muted font-mono">{zones.length} Sectors Monitored</span>
        </div>

        <div className="grid grid-cols-5 gap-1.5">
          {zones.map((z) => {
            const isSelected = z.id === selectedZoneId;
            const isCriticalOrHigh = z.risk_band === 'CRITICAL' || z.risk_band === 'HIGH';

            return (
              <button
                key={z.id}
                onClick={() => selectZone(z.id)}
                className={`py-1.5 px-2 rounded-lg text-xs font-bold font-mono transition-all flex flex-col items-center justify-center relative ${
                  isSelected
                    ? 'bg-talus-600 text-white shadow-sm border border-talus-700'
                    : 'bg-mine-darker hover:bg-mine-dark text-mine-text border border-mine-border'
                }`}
              >
                <span>Zone {z.id}</span>
                <span
                  className={`text-[9px] font-normal ${
                    z.risk_band === 'CRITICAL'
                      ? 'text-risk-critical font-bold'
                      : z.risk_band === 'HIGH'
                      ? 'text-risk-high font-bold'
                      : z.risk_band === 'MODERATE'
                      ? 'text-risk-moderate'
                      : 'text-risk-verylow'
                  }`}
                >
                  {z.risk_score}
                </span>
                {isCriticalOrHigh && (
                  <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-risk-critical animate-ping"></span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Zone Header */}
      <div className="border-t border-mine-border pt-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-[11px] text-talus-600 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <span>{zone.sector || 'Open-Pit Highwall'}</span>
            <ChevronRight className="w-3 h-3 text-mine-muted" />
            <span className="text-mine-muted">{zone.benches || 'Benches 05–08'}</span>
          </div>
          <h2 className="text-lg font-extrabold text-mine-text tracking-tight mt-0.5">
            {zone.name}
          </h2>
        </div>

        <div className="text-right">
          <div className="text-[10px] text-mine-muted">Status</div>
          <div
            className={`text-xs font-bold uppercase ${
              zone.risk_band === 'CRITICAL' || zone.risk_band === 'HIGH'
                ? 'text-risk-critical animate-pulse'
                : 'text-mine-text'
            }`}
          >
            {zone.status || 'Active Operations'}
          </div>
        </div>
      </div>

      {/* 1. Risk Score Gauge & Confidence */}
      <RiskScoreGauge
        score={zone.risk_score}
        band={zone.risk_band}
        confidence={zone.confidence}
        trend={zone.trend}
        isSimulated={zone.isSimulated || (activeSimulation && activeSimulation.zone_id === zone.id)}
      />

      {/* 2. Role-Based Dynamic Action Card */}
      <RoleActionCard
        roleActions={zone.role_actions}
        zoneName={zone.name}
        riskBand={zone.risk_band}
      />

      {/* 3. SHAP Feature Contribution (Why is this risk high?) */}
      <ShapChart
        shap={zone.shap}
        baseRisk={zone.base_risk || 15}
        currentRisk={zone.risk_score}
        zoneName={zone.name}
      />

      {/* 4. Risk Escalation Timeline */}
      <RiskTrendChart trend={zone.trend} zoneName={zone.name} />

      {/* 5. Missing Evidence & Uncertainty Warning */}
      <MissingEvidenceCard
        missingEvidence={zone.missing_evidence}
        confidence={zone.confidence}
        warningText={zone.missing_evidence_warning}
      />
    </div>
  );
}
