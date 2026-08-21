import React, { useState, useEffect } from 'react';
import { useMineContext } from '../../context/MineContext';
import RoleSelector from './RoleSelector';
import {
  Activity,
  Sliders,
  Navigation,
  Eye,
  RotateCcw,
  Bell,
  Radio,
  Clock,
  Layers,
  Sparkles
} from 'lucide-react';

export default function Header() {
  const {
    unacknowledgedAlertsCount,
    setIsWhatIfOpen,
    setIsRouteModalOpen,
    setIsCvModalOpen,
    setIsAlertsDrawerOpen,
    activeSimulation,
    resetSimulation,
  } = useMineContext();

  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="bg-mine-darker/95 border-b border-mine-border/80 sticky top-0 z-40 backdrop-blur-md px-4 py-2.5">
      <div className="max-w-[1920px] mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Left: Brand & Tagline */}
        <div className="flex items-center gap-3.5">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-talus-500 to-talus-700 flex items-center justify-center shadow-lg shadow-talus-500/20 border border-talus-400/30">
              <Activity className="w-5 h-5 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold tracking-wider text-lg text-white font-mono flex items-center gap-1.5">
                  TALUS
                  <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-talus-500/20 text-talus-300 border border-talus-500/30">
                    SIH 2026
                  </span>
                </span>
                {/* Demo mode badge */}
                <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-800 text-[10px] font-medium text-slate-300 border border-slate-700">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  DEMO MODE — Synthetic / Historical Data
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">
                Risk-Aware Decision Support for Open-Pit Mine Safety
              </p>
            </div>
          </div>
        </div>

        {/* Center: Command Actions (Simulation, Routing, CV Inspector) */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* What-If Simulator Button */}
          <button
            onClick={() => setIsWhatIfOpen(true)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              activeSimulation
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-lg shadow-amber-500/10 animate-pulse'
                : 'bg-mine-card hover:bg-mine-dark text-slate-200 border-mine-border hover:border-talus-500/40'
            }`}
            title="Open geotechnical condition simulator"
          >
            <Sliders className="w-3.5 h-3.5 text-amber-400" />
            <span>What-If Simulator</span>
            {activeSimulation && (
              <span className="w-2 h-2 rounded-full bg-amber-400 ml-0.5"></span>
            )}
          </button>

          {/* Safe Routing Button */}
          <button
            onClick={() => setIsRouteModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-mine-card hover:bg-mine-dark text-slate-200 border border-mine-border hover:border-talus-500/40 transition-all"
            title="Calculate and compare risk-aware evacuation & haulage routes"
          >
            <Navigation className="w-3.5 h-3.5 text-emerald-400" />
            <span>Safe Route</span>
          </button>

          {/* CV Crack Inspector Button */}
          <button
            onClick={() => setIsCvModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-mine-card hover:bg-mine-dark text-slate-200 border border-mine-border hover:border-talus-500/40 transition-all"
            title="Inspect drone-based highwall crack segmentation and feature extraction"
          >
            <Eye className="w-3.5 h-3.5 text-talus-400" />
            <span>CV Crack Analysis</span>
          </button>

          {/* Reset Baseline if active simulation */}
          {activeSimulation && (
            <button
              onClick={resetSimulation}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-red-500/10 hover:bg-red-500/20 text-red-300 border border-red-500/30 transition-all"
              title="Reset simulated conditions back to pit baseline telemetry"
            >
              <RotateCcw className="w-3 h-3 text-red-400" />
              <span>Reset Sim</span>
            </button>
          )}
        </div>

        {/* Right: Active Alerts, Role Selector, Clock & Status */}
        <div className="flex items-center gap-3">
          {/* Active Alerts Drawer Trigger */}
          <button
            onClick={() => setIsAlertsDrawerOpen(true)}
            className="relative p-2 bg-mine-card hover:bg-mine-dark border border-mine-border hover:border-slate-600 rounded-lg text-slate-300 hover:text-white transition-all group"
            title="View Active Risk Escalation Alerts"
          >
            <Bell className="w-4 h-4 group-hover:text-amber-400 transition-colors" />
            {unacknowledgedAlertsCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-white font-bold text-[10px] flex items-center justify-center ring-2 ring-mine-darkest animate-pulse">
                {unacknowledgedAlertsCount}
              </span>
            )}
          </button>

          {/* Role-Specific Perspective Selector */}
          <RoleSelector />

          {/* Pit Telemetry & Clock */}
          <div className="hidden lg:flex flex-col items-end pl-2 border-l border-mine-border/80 text-right font-mono">
            <div className="flex items-center gap-1.5 text-[11px] text-slate-300">
              <Clock className="w-3 h-3 text-slate-400" />
              <span>{currentTime.toLocaleTimeString('en-US', { hour12: false })}</span>
              <span className="text-[9px] text-slate-400 font-sans">IST</span>
            </div>
            <div className="flex items-center gap-1 text-[10px] text-emerald-400 font-sans">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Telemetry Live
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
