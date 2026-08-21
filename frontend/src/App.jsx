import React from 'react';
import { MineProvider } from './context/MineContext';
import Header from './components/Header/Header';
import Dashboard from './pages/Dashboard';
import { ShieldCheck, Info } from 'lucide-react';

export default function App() {
  return (
    <MineProvider>
      <div className="min-h-screen bg-mine-darkest flex flex-col font-sans selection:bg-talus-500 selection:text-white">
        {/* Command Center Top Navigation */}
        <Header />

        {/* Core Decision Support Workspace */}
        <div className="flex-1">
          <Dashboard />
        </div>

        {/* Industrial Command Center Footer */}
        <footer className="mt-8 border-t border-mine-border/80 bg-mine-darker/90 py-3 px-4 text-slate-400 text-xs">
          <div className="max-w-[1920px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-talus-400" />
              <span className="font-semibold text-slate-300">
                TALUS — Mine Safety Intelligence Decision Support System
              </span>
              <span className="text-slate-500 font-mono">|</span>
              <span className="text-slate-400 text-[11px]">
                SIH 2026 Prototype
              </span>
            </div>

            <div className="flex items-center gap-3 text-[11px] text-slate-400">
              <span>
                Engineered for: <strong>Open-Pit & Opencast Mine Highwall Risk</strong>
              </span>
              <span className="text-slate-500 font-mono">|</span>
              <span className="text-talus-400 font-mono">
                Frozen Model v1 · Generator v1.4.0 · Scenario Engine v1.5
              </span>
            </div>
          </div>
        </footer>
      </div>
    </MineProvider>
  );
}
