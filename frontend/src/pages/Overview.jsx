import React from 'react';
import { Link } from 'react-router-dom';
import { useTalusContext } from '../context/TalusContext';
import { Users, Shield, Briefcase, Flame, ArrowRight } from 'lucide-react';

export default function Overview() {
  const { locationData, t } = useTalusContext();
  const ROLES = [
    { to: '/role/villager', icon: Users, title: t('overview.role_villager_t'), desc: t('overview.role_villager_d') },
    { to: '/role/district_officer', icon: Shield, title: t('overview.role_district_t'), desc: t('overview.role_district_d') },
    { to: '/role/state_manager', icon: Briefcase, title: t('overview.role_state_t'), desc: t('overview.role_state_d') },
    { to: '/role/rescue_team', icon: Flame, title: t('overview.role_rescue_t'), desc: t('overview.role_rescue_d') },
  ];
  return (
    <main className="max-w-[900px] mx-auto px-3 sm:px-4 py-10 space-y-6 text-center">
      <div>
        <h1 className="text-2xl font-extrabold text-mine-text">{t('overview.title')}</h1>
        <p className="text-sm text-mine-muted mt-1">
          {t('overview.subtitle')} ({locationData.label})
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
        {ROLES.map(({ to, icon: Icon, title, desc }) => (
          <Link
            key={to}
            to={to}
            className="p-5 bg-mine-card border border-mine-border rounded-2xl hover:border-talus-500 transition-all group"
          >
            <Icon className="w-6 h-6 text-talus-600" />
            <div className="text-sm font-extrabold text-mine-text mt-2 flex items-center gap-1">
              {title}
              <ArrowRight className="w-3.5 h-3.5 text-mine-muted group-hover:text-talus-600 group-hover:translate-x-0.5 transition-all" />
            </div>
            <div className="text-xs text-mine-muted mt-1">{desc}</div>
          </Link>
        ))}
      </div>
      <p className="text-[11px] text-mine-muted">
        {t('overview.note')}
      </p>
    </main>
  );
}
