import React from 'react';
import { MineProvider } from './context/MineContext';
import Header from './components/Header/Header';
import Dashboard from './pages/Dashboard';
import { ShieldCheck, Info } from 'lucide-react';

export default function App() {
  return (
    <MineProvider>
      <div className="min-h-screen bg-mine-darkest flex flex-col font-sans selection:bg-talus-600 selection:text-white">
        {/* Command Center Top Navigation */}
        <Header />

        {/* Core Decision Support Workspace */}
        <div className="flex-1">
          <Dashboard />
        </div>

        {/* Industrial Command Center Footer */}
        <footer className="mt-8 border-t border-mine-border bg-mine-darker py-3 px-4 text-mine-muted text-xs">
          <div className="max-w-[1920px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-talus-600" />
              <span className="font-semibold text-mine-text">
                TALUS — Mine Safety Intelligence Decision Support System
              </span>
              <span className="text-mine-muted font-mono">|</span>
              <span className="text-mine-muted text-[11px]">
                SIH 2026 Prototype
              </span>
            </div>

            <div className="flex items-center gap-3 text-[11px] text-mine-muted">
              <span>
                Engineered for: <strong className="text-mine-text">Open-Pit & Opencast Mine Highwall Risk</strong>
              </span>
              <span className="text-mine-muted font-mono">|</span>
              <span className="text-talus-600 font-mono font-medium">
                React • Leaflet • Recharts • FastAPI Contract Ready
              </span>
            </div>
          </div>
        </footer>
      </div>
    </MineProvider>
  );
}
