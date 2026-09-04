import React, { useEffect } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import RiskMap from '../../components/RiskMap/RiskMap';
import { ShieldAlert, Navigation, FileText, Globe } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function VillagerPage() {
  const { zones, selectedZoneData, locationData, t, setRole, lang } = useTalusContext();
  useEffect(() => setRole('villager'), []);
  const zone = selectedZoneData;
  const isCritical = zone?.risk_band === 'CRITICAL' || zone?.risk_band === 'HIGH';
  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      {/* Simple header — no % */}
      <div className={`rounded-2xl p-4 border text-center space-y-2 ${isCritical ? 'bg-risk-critical/10 border-risk-critical/40' : 'bg-mine-card border-mine-border'}`}>
        <div className="flex items-center justify-center gap-2">
          <ShieldAlert className={`w-6 h-6 ${isCritical ? 'text-risk-critical' : 'text-risk-verylow'}`} />
          <span className={`text-lg font-extrabold ${isCritical ? 'text-risk-critical' : 'text-mine-text'}`}>{zone?.name || locationData.label}</span>
          <span className={`px-2 py-0.5 rounded text-xs font-bold ${isCritical ? 'bg-risk-critical text-white' : 'bg-risk-verylow text-white'}`}>{zone?.risk_band || '—'}</span>
        </div>
        <p className="text-sm font-bold text-mine-text leading-relaxed">
          {zone?.role_actions?.villager?.action || zone?.role_actions?.['villager']?.action || t('role.villager') + ' — ' + (isCritical ? t('villager.avoid_msg') : t('villager.no_restriction'))}
        </p>
        <p className="text-xs text-mine-muted">{t('app.provenance').split('.')[0]}.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-7 h-[560px]"><RiskMap /></div>
        <div className="lg:col-span-5 space-y-3">
          <div className="bg-mine-card border border-mine-border rounded-2xl p-4 space-y-3">
            <h3 className="text-sm font-bold text-mine-text flex items-center gap-1.5"><Navigation className="w-4 h-4 text-talus-600" /> {t('header.safeRoute')}</h3>
            <p className="text-xs text-mine-muted">{t('villager.tap_map')}</p>
            <Link to="/routes" className="block w-full text-center py-2 bg-talus-600 hover:bg-talus-500 text-white rounded-lg text-xs font-bold">{t('villager.safe_route_btn')}</Link>
            <Link to="/reports" className="block w-full text-center py-2 bg-mine-darker border border-mine-border rounded-lg text-xs font-semibold flex items-center justify-center gap-1"><FileText className="w-3.5 h-3.5" /> {t('villager.submit_report_btn')}</Link>
          </div>
          <div className="bg-mine-darker border border-mine-border rounded-xl p-3 flex items-center gap-2 text-xs">
            <Globe className="w-4 h-4 text-talus-600" />
            <span className="text-mine-text font-semibold">{lang === 'ne' ? 'नेपाली / हिन्दी / English' : lang === 'hi' ? 'हिन्दी / नेपाली / English' : 'English / हिन्दी / नेपाली'}</span>
            <span className="ml-auto text-mine-muted">{t('villager.alerts_mother')}</span>
          </div>
        </div>
      </div>
    </main>
  );
}
