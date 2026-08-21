import React, { useState, useRef, useEffect } from 'react';
import { useMineContext } from '../../context/MineContext';
import { ROLES } from '../../data/mockData';
import { Shield, HardHat, Briefcase, Flame, ChevronDown, Check } from 'lucide-react';

const ROLE_ICONS = {
  safety_officer: Shield,
  worker: HardHat,
  mine_manager: Briefcase,
  rescue_team: Flame,
};

export default function RoleSelector() {
  const { role, setRole, currentRoleMeta } = useMineContext();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

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
        className="flex items-center gap-2.5 px-3 py-1.5 bg-mine-card hover:bg-mine-dark border border-mine-border hover:border-talus-500/50 rounded-lg text-slate-200 transition-all text-xs font-medium shadow-sm group"
        title="Switch user perspective to view tailored actions"
      >
        <div className="w-5 h-5 rounded bg-talus-500/20 text-talus-400 flex items-center justify-center group-hover:bg-talus-500/30 transition-colors">
          <IconComponent className="w-3.5 h-3.5" />
        </div>
        <div className="text-left leading-none">
          <div className="text-[10px] text-slate-400 font-normal">Active Role</div>
          <div className="font-semibold text-slate-100 mt-0.5">{currentRoleMeta.label}</div>
        </div>
        <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-mine-card border border-mine-border rounded-xl shadow-2xl z-50 overflow-hidden backdrop-blur-md">
          <div className="px-3 py-2 bg-mine-darker border-b border-mine-border text-[11px] font-medium text-slate-400 uppercase tracking-wider">
            Select Decision Perspective
          </div>
          <div className="p-1.5 space-y-1">
            {ROLES.map((r) => {
              const RoleIcon = ROLE_ICONS[r.id] || Shield;
              const isSelected = r.id === role;
              return (
                <button
                  key={r.id}
                  onClick={() => {
                    setRole(r.id);
                    setIsOpen(false);
                  }}
                  className={`w-full flex items-start gap-2.5 p-2.5 rounded-lg text-left transition-all ${
                    isSelected
                      ? 'bg-talus-600/20 border border-talus-500/40 text-talus-200'
                      : 'hover:bg-mine-dark/80 text-slate-300 border border-transparent'
                  }`}
                >
                  <div
                    className={`w-7 h-7 rounded-md flex items-center justify-center shrink-0 mt-0.5 ${
                      isSelected ? 'bg-talus-500 text-white' : 'bg-mine-border text-slate-400'
                    }`}
                  >
                    <RoleIcon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-100">{r.label}</span>
                      {isSelected && <Check className="w-3.5 h-3.5 text-talus-400" />}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">{r.description}</p>
                  </div>
                </button>
              );
            })}
          </div>
          <div className="px-3 py-2 bg-mine-darker/60 border-t border-mine-border/50 text-[10px] text-slate-400 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-talus-400"></span>
            All risk intelligence dynamically adapts to role protocols.
          </div>
        </div>
      )}
    </div>
  );
}
