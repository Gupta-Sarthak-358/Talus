import React from 'react';
import { Link } from 'react-router-dom';
import { useTalusContext } from '../context/TalusContext';
import { Users, Shield, Briefcase, Flame, ArrowRight } from 'lucide-react';

const ROLES = [
  { to: '/role/villager', icon: Users, title: 'Villager / Community', desc: 'Danger or safe? Which road to avoid, in your language.' },
  { to: '/role/district_officer', icon: Shield, title: 'District Officer', desc: 'Close stretches, evacuate first, review field queue.' },
  { to: '/role/state_manager', icon: Briefcase, title: 'State Manager (SSDMA)', desc: 'Triage across Gangtok / Lachung / Darjeeling.' },
  { to: '/role/rescue_team', icon: Flame, title: 'Rescue Team (NDRF/SDRF)', desc: 'Safe ingress corridor — strictly bypass R2.' },
];

export default function Overview() {
  const { locationData } = useTalusContext();
  return (
    <main className="max-w-[900px] mx-auto px-3 sm:px-4 py-10 space-y-6 text-center">
      <div>
        <h1 className="text-2xl font-extrabold text-mine-text">Who are you?</h1>
        <p className="text-sm text-mine-muted mt-1">
          Talus shows each person only what they need — {locationData.label}. Pick your role to continue.
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
        Tool views (/map /reports /lab /routes) still exist as deep links from inside each role page — admin panel later.
      </p>
    </main>
  );
}
