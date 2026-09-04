import React, { useState, useRef, useEffect } from 'react';
import { useMineContext } from '../../context/MineContext';
import { Languages, Check, ChevronDown } from 'lucide-react';

export default function LanguageSelector() {
  const { lang, setLang, supportedLangs } = useMineContext();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function handleOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, []);

  const active = supportedLangs.find(l => l.id === lang) || supportedLangs[0];

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-2.5 py-1.5 bg-mine-card hover:bg-mine-dark border border-mine-border hover:border-talus-500 rounded-lg text-mine-text transition-all text-xs font-medium shadow-sm"
        title="Change language — English / हिन्दी / नेपाली"
      >
        <Languages className="w-3.5 h-3.5 text-talus-600" />
        <span className="hidden sm:inline font-semibold">{active.native}</span>
        <span className="sm:hidden font-mono font-bold">{active.flag}</span>
        <ChevronDown className={`w-3 h-3 text-mine-muted transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-48 bg-mine-card border border-mine-border rounded-xl shadow-xl z-50 overflow-hidden">
          <div className="px-3 py-2 bg-mine-darker border-b border-mine-border text-[11px] font-medium text-mine-muted uppercase tracking-wider">
            Select Language
          </div>
          {supportedLangs.map((l) => {
            const isActive = l.id === lang;
            return (
              <button
                key={l.id}
                onClick={() => { setLang(l.id); setOpen(false); }}
                className={`w-full flex items-center justify-between px-3 py-2.5 text-left text-xs hover:bg-mine-darker transition-colors ${isActive ? 'bg-talus-600/10 text-talus-700 font-semibold' : 'text-mine-text'}`}
              >
                <span className="flex items-center gap-2">
                  <span className="w-7 h-7 rounded bg-mine-darker border border-mine-border flex items-center justify-center font-mono text-[11px] font-bold">{l.flag}</span>
                  <span>
                    <span className="block font-semibold">{l.native}</span>
                    <span className="block text-[10px] text-mine-muted">{l.label}</span>
                  </span>
                </span>
                {isActive && <Check className="w-4 h-4 text-talus-600" />}
              </button>
            );
          })}
          <div className="px-3 py-2 bg-mine-darker border-t border-mine-border text-[10px] text-mine-muted">
            Alerts dispatched in selected language via <code className="font-mono">POST /api/alerts/dispatch</code>
          </div>
        </div>
      )}
    </div>
  );
}
