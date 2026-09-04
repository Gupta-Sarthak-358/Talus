import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import Header from './Header/Header';
import { useTalusContext } from '../context/TalusContext';
import { ShieldCheck, Info } from 'lucide-react';
import { LayoutDashboard, Map, FileText, FlaskConical, Navigation, Users, Shield, Briefcase, Flame } from 'lucide-react';

const TABS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/map', label: 'GIS Map', icon: Map },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/lab', label: 'Lab', icon: FlaskConical },
  { to: '/routes', label: 'Routes', icon: Navigation },
];

const ROLE_TABS = [
  { to: '/role/villager', label: 'Villager', icon: Users },
  { to: '/role/district_officer', label: 'District', icon: Shield },
  { to: '/role/state_manager', label: 'State', icon: Briefcase },
  { to: '/role/rescue_team', label: 'Rescue', icon: Flame },
];

function Footer() {
  const { t, locationData } = useTalusContext();
  return (
    <footer className="mt-8 border-t border-mine-border bg-mine-darker py-4 px-4 text-mine-muted text-xs">
      <div className="max-w-[1920px] mx-auto space-y-2">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-2 border-b border-mine-border pb-2.5">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-talus-600" />
            <span className="font-semibold text-mine-text">{t('app.footerTitle')}</span>
            <span className="text-mine-muted font-mono">|</span>
            <span className="text-talus-600 font-mono text-[11px] font-bold">SIH26001 / MDoNER Prototype</span>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-mine-muted">
            <span>Region: <strong className="text-mine-text">{locationData.label} ({locationData.zones.map(z=>z.id).join('–')})</strong></span>
            <span className="text-mine-muted font-mono">|</span>
            <span className="text-talus-600 font-mono font-medium">{t('app.footerModel')}</span>
          </div>
        </div>
        <div className="text-[11px] text-mine-muted space-y-1 pt-0.5 leading-relaxed">
          <div className="flex items-start gap-1.5">
            <Info className="w-3.5 h-3.5 text-talus-600 shrink-0 mt-0.5" />
            <span><strong className="text-mine-text">Data Provenance:</strong> {t('app.provenance')}</span>
          </div>
          <div className="pl-5 text-[10px] text-mine-muted/90 font-mono">{t('app.disclaimer')}</div>
        </div>
      </div>
    </footer>
  );
}

export default function Layout() {
  const location = useLocation();
  return (
    <div className="min-h-screen bg-mine-darkest flex flex-col font-sans selection:bg-talus-600 selection:text-white">
      <Header />
      {/* Tab bar — second nav, URL-shareable */}
      <nav className="bg-mine-darker border-b border-mine-border px-3 sm:px-4">
        <div className="max-w-[1920px] mx-auto flex items-center gap-1 py-1.5 overflow-x-auto">
          {TABS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-talus-600 text-white border-talus-700 shadow-sm'
                    : 'bg-mine-card text-mine-text border-mine-border hover:border-talus-500'
                }`
              }
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{label}</span>
            </NavLink>
          ))}
          <span className="hidden md:block w-px h-5 bg-mine-border mx-1" />
          {ROLE_TABS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-emerald-600 text-white border-emerald-700 shadow-sm'
                    : 'bg-mine-card text-mine-muted border-mine-border hover:border-emerald-500'
                }`
              }
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{label}</span>
            </NavLink>
          ))}
          <span className="ml-auto hidden sm:flex items-center gap-1 text-[11px] text-mine-muted font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            {location.pathname}
          </span>
        </div>
      </nav>
      <div className="flex-1">
        <Outlet />
      </div>
      <Footer />
    </div>
  );
}
