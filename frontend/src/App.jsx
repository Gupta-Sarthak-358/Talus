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

        {/* Industrial Command Center Footer with Contract Provenance Footnote */}
        <footer className="mt-8 border-t border-mine-border bg-mine-darker py-4 px-4 text-mine-muted text-xs">
          <div className="max-w-[1920px] mx-auto space-y-2">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-2 border-b border-mine-border pb-2.5">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-talus-600" />
                <span className="font-semibold text-mine-text">
                  TALUS — NER Landslide Early Warning & Decision Support System
                </span>
                <span className="text-mine-muted font-mono">|</span>
                <span className="text-talus-600 font-mono text-[11px] font-bold">
                  SIH26001 / MDoNER Prototype
                </span>
              </div>

              <div className="flex items-center gap-3 text-[11px] text-mine-muted">
                <span>
                  Region: <strong className="text-mine-text">Gangtok Corridor, Sikkim (S1–S4)</strong>
                </span>
                <span className="text-mine-muted font-mono">|</span>
                <span className="text-talus-600 font-mono font-medium">
                  Frozen Model v1 (17 features) · Scenarios v1.5
                </span>
              </div>
            </div>

            {/* Mandatory Provenance & Operational Footnote (Always Visible on Screen 1) */}
            <div className="text-[11px] text-mine-muted space-y-1 pt-0.5 leading-relaxed">
              <div className="flex items-start gap-1.5">
                <Info className="w-3.5 h-3.5 text-talus-600 shrink-0 mt-0.5" />
                <span>
                  <strong className="text-mine-text">Data Provenance:</strong> IMD rainfall + SRTM DEM + GSI Bhusanket + ERA5 soil moisture + Sentinel-2 NDVI/LULC + OSM roads/rivers. Soil = reanalysis proxy. Sensor = recorded fixture. Bands = prototype, not safety standard.
                </span>
              </div>
              <div className="pl-5 text-[10px] text-mine-muted/90 font-mono">
                Disclaimer: scores = susceptibility under prototype target, not P(landslide tomorrow); soil = reanalysis proxy; sensor = fixture; bands = prototype, not safety standard.
              </div>
            </div>
          </div>
        </footer>
      </div>
    </MineProvider>
  );
}
