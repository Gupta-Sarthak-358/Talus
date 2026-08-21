import React from 'react';
import { useMineContext } from '../../context/MineContext';
import { Shield, HardHat, Briefcase, Flame, Navigation, AlertCircle, ArrowRight, CheckCircle } from 'lucide-react';

const ROLE_ICONS = {
  safety_officer: Shield,
  worker: HardHat,
  mine_manager: Briefcase,
  rescue_team: Flame,
};

export default function RoleActionCard({ roleActions = {}, zoneName = 'Zone B', riskBand = 'HIGH' }) {
  const { role, currentRoleMeta, setIsRouteModalOpen, setIsWhatIfOpen, setIsCvModalOpen } = useMineContext();

  const action = roleActions[role] || {
    header: 'STANDARD OPERATIONAL PROTOCOL',
    action: 'Maintain standard visual monitoring.',
    caution: 'Check highwall berms regularly.',
    routeRecommended: 'Standard Pit Route',
    urgency: 'Normal',
  };

  const RoleIcon = ROLE_ICONS[role] || Shield;
  const isHighRisk = riskBand === 'HIGH' || riskBand === 'CRITICAL';

  return (
    <div
      className={`rounded-xl p-4 border shadow-sm space-y-3 transition-all ${
        isHighRisk
          ? 'bg-mine-darker border-risk-high/40'
          : 'bg-mine-darker border-mine-border'
      }`}
    >
      {/* Header with Role Tag */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-talus-600/15 text-talus-600 flex items-center justify-center">
            <RoleIcon className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-bold tracking-wider text-talus-600">
              Role Directive: {currentRoleMeta.label}
            </div>
            <h4 className="text-xs font-extrabold text-mine-text uppercase tracking-wide">
              {action.header}
            </h4>
          </div>
        </div>

        <span
          className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
            action.urgency === 'Immediate Action' || action.urgency === 'High Priority'
              ? 'bg-risk-critical/15 text-risk-critical border border-risk-critical/30 animate-pulse'
              : 'bg-mine-card text-mine-muted border border-mine-border'
          }`}
        >
          {action.urgency || 'Operational'}
        </span>
      </div>

      {/* Action Directive Content */}
      <div className="bg-mine-card p-3 rounded-lg border border-mine-border space-y-2">
        <div className="text-xs font-semibold text-mine-text flex items-start gap-2">
          <span className="text-talus-600 font-bold shrink-0">▶</span>
          <span>{action.action}</span>
        </div>

        {action.caution && (
          <div className="text-[11px] text-mine-text flex items-start gap-2 bg-risk-moderate/15 p-2 rounded border border-risk-moderate/30">
            <AlertCircle className="w-3.5 h-3.5 text-risk-moderate shrink-0 mt-0.5" />
            <span>{action.caution}</span>
          </div>
        )}

        <div className="text-[11px] text-mine-muted flex items-center justify-between pt-1 border-t border-mine-border">
          <span>Recommended Route Corridor:</span>
          <span className="font-semibold text-risk-verylow font-mono">
            {action.routeRecommended}
          </span>
        </div>
      </div>

      {/* Quick Action Button according to role */}
      <div className="pt-1 flex gap-2">
        {role === 'worker' && (
          <button
            onClick={() => setIsRouteModalOpen(true)}
            className="w-full flex items-center justify-center gap-1.5 py-2 bg-talus-600 hover:bg-talus-500 text-white rounded-lg text-xs font-bold transition-all shadow-sm"
          >
            <Navigation className="w-3.5 h-3.5" />
            <span>Request Safe Evacuation Route</span>
          </button>
        )}

        {role === 'safety_officer' && (
          <button
            onClick={() => setIsCvModalOpen(true)}
            className="w-full flex items-center justify-center gap-1.5 py-2 bg-talus-600 hover:bg-talus-500 text-white rounded-lg text-xs font-bold transition-all shadow-sm"
          >
            <Shield className="w-3.5 h-3.5" />
            <span>Launch Geotechnical Drone / CV Inspection</span>
          </button>
        )}

        {role === 'mine_manager' && (
          <button
            onClick={() => setIsRouteModalOpen(true)}
            className="w-full flex items-center justify-center gap-1.5 py-2 bg-talus-600 hover:bg-talus-500 text-white rounded-lg text-xs font-bold transition-all shadow-sm"
          >
            <Briefcase className="w-3.5 h-3.5" />
            <span>Re-Route Fleet Dispatch Around Zone</span>
          </button>
        )}

        {role === 'rescue_team' && (
          <button
            onClick={() => setIsRouteModalOpen(true)}
            className="w-full flex items-center justify-center gap-1.5 py-2 bg-risk-critical hover:bg-risk-critical/90 text-white rounded-lg text-xs font-bold transition-all shadow-sm"
          >
            <Flame className="w-3.5 h-3.5" />
            <span>View Safe Staging & Approach Corridors</span>
          </button>
        )}
      </div>
    </div>
  );
}
