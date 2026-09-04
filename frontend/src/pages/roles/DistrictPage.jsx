import React, { useEffect } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import RiskMap from '../../components/RiskMap/RiskMap';
import ZoneIntelligencePanel from '../../components/ZoneDetails/ZoneIntelligencePanel';
import RoadStatusCard from '../../components/Routing/RoadStatusCard';
import { FileText, Bell } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function DistrictPage() {
  const { setRole, zones, t } = useTalusContext();
  useEffect(() => setRole('district_officer'), []);
  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <div className="bg-mine-darker border border-mine-border rounded-xl px-4 py-2 flex flex-wrap items-center justify-between gap-2 text-xs">
        <span className="font-bold text-mine-text">{t('role.district_officer')} — Closure & Evacuation</span>
        <span className="text-mine-muted">{zones.length} slopes · live · score + calibrated % + SHAP drivers</span>
      </div>
      {/* Officer primary workflow first — queue above map */}
      <div className="flex gap-2">
        <Link to="/reports" className="flex-1 py-2 bg-talus-600 text-white rounded-lg text-xs font-bold text-center flex items-center justify-center gap-1"><FileText className="w-3.5 h-3.5" /> Review Field Queue & Submit</Link>
        <Link to="/reports" className="px-3 py-2 bg-mine-darker border border-mine-border rounded-lg text-xs font-semibold flex items-center gap-1"><Bell className="w-3.5 h-3.5" /> Multi-Lang Alerts</Link>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        <div className="lg:col-span-7 h-[640px] sticky top-[88px]"><RiskMap /></div>
        <div className="lg:col-span-5 space-y-4"><ZoneIntelligencePanel /></div>
      </div>
      <RoadStatusCard />
    </main>
  );
}
