import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTalusContext } from '../../context/TalusContext';
import { ROLES } from '../../data/constants';
import { Shield, Users, Briefcase, Flame, ChevronDown, Check } from 'lucide-react';

const ROLE_ICONS = {
  villager: Users,
  district_officer: Shield,
  state_manager: Briefcase,
  rescue_team: Flame,
};

export default function RoleSelector() {
  const { role, setRole, currentRoleMeta, t } = useTalusContext();
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const pickRole = (newRole) => {
    setRole(newRole);
    setIsOpen(false);
    // Demo: choosing a role shows its dedicated page (admin panel later)
    if (location.pathname.startsWith('/role/') || location.pathname === '/') {
      navigate(`/role/${newRole}`);
    }
  };

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const IconComponent = ROLE_ICONS[role] || Shield;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2.5 px-3 py-1.5 bg-mine-card hover:bg-mine-dark border border-mine-border hover:border-talus-500 rounded-lg text-mine-text transition-all text-xs font-medium shadow-sm group"
        title="Switch user perspective to view tailored actions"
      >
        <div className="w-5 h-5 rounded bg-talus-600/15 text-talus-600 flex items-center justify-center group-hover:bg-talus-600/25 transition-colors">
          <IconComponent className="w-3.5 h-3.5" />
        </div>
        <div className="text-left leading-none">
          <div className="text-[10px] text-mine-muted font-normal">{t('role.active')}</div>
          <div className="font-semibold text-mine-text mt-0.5">{t(`role.${role}`) || currentRoleMeta.label}</div>
        </div>
        <ChevronDown className={`w-3.5 h-3.5 text-mine-muted transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-mine-card border border-mine-border rounded-xl shadow-xl z-50 overflow-hidden">
          <div className="px-3 py-2 bg-mine-darker border-b border-mine-border text-[11px] font-medium text-mine-muted uppercase tracking-wider">
            {t('role.selectPerspective')}
          </div>
          <div className="p-1.5 space-y-1">
            {ROLES.map((r) => {
              const RoleIcon = ROLE_ICONS[r.id] || Shield;
              const isSelected = r.id === role;
              return (
                <button
                  key={r.id}
                  onClick={() => pickRole(r.id)}
                  className={`w-full flex items-start gap-2.5 p-2.5 rounded-lg text-left transition-all ${
                    isSelected
                      ? 'bg-talus-600 border border-talus-700 text-white'
                      : 'hover:bg-mine-darker text-mine-text border border-transparent'
                  }`}
                >
                  <div
                    className={`w-7 h-7 rounded-md flex items-center justify-center shrink-0 mt-0.5 ${
                      isSelected ? 'bg-talus-700 text-white' : 'bg-mine-dark text-talus-600'
                    }`}
                  >
                    <RoleIcon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className={`text-xs font-semibold ${isSelected ? 'text-white' : 'text-mine-text'}`}>{t(`role.${r.id}`)}</span>
                      {isSelected && <Check className="w-3.5 h-3.5 text-talus-100" />}
                    </div>
                    <p className={`text-[11px] mt-0.5 leading-snug ${isSelected ? 'text-talus-100/90' : 'text-mine-muted'}`}>{t(`role.${r.id}`) === r.label ? r.description : t(`role.${r.id}_desc`) || r.description}</p>
                  </div>
                </button>
              );
            })}
          </div>
          <div className="px-3 py-2 bg-mine-darker border-t border-mine-border text-[10px] text-mine-muted flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-talus-600"></span>
            All risk intelligence dynamically adapts to role protocols.
          </div>
        </div>
      )}
    </div>
  );
}
