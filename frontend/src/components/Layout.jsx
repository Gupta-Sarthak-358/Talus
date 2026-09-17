import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import Header from './Header/Header';
import { useTalusContext } from '../context/TalusContext';
import { ShieldCheck } from 'lucide-react';

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
            <span>{t('app.region')}: <strong className="text-mine-text">{(t(`location.${locationData?.id}`) !== `location.${locationData?.id}` ? t(`location.${locationData.id}`) : locationData?.label) || 'Gangtok'} ({(locationData?.zones||[]).map(z=>z.id).join('–')})</strong></span>
            <span className="text-mine-muted font-mono">|</span>
            <span className="text-talus-600 font-mono font-medium">{t('app.footerModel')}</span>
          </div>
        </div>

      </div>
    </footer>
  );
}

export default function Layout() {
  const { t } = useTalusContext();
  return (
    <div className="min-h-screen bg-mine-darkest flex flex-col font-sans selection:bg-talus-600 selection:text-white">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 bg-white border-2 border-zinc-900 px-3 py-2 rounded-xl text-xs font-bold z-[9999]">{t('common.skip_content')}</a>
      <Header />
      <main id="main" className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
