import React, { useState, useEffect } from 'react';
import { useMineContext } from '../../context/MineContext';
import RoleSelector from './RoleSelector';
import LocationSelector from './LocationSelector';
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
  Sparkles,
  FileText
} from 'lucide-react';

export default function Header() {
  const {
    unacknowledgedAlertsCount,
    setIsWhatIfOpen,
    setIsRouteModalOpen,
    setIsCvModalOpen,
    setIsAlertsDrawerOpen,
    setIsReportModalOpen,
    reports,
    activeSimulation,
    resetSimulation,
  } = useMineContext();

  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="bg-mine-darker border-b border-mine-border sticky top-0 z-40 px-4 py-2.5 shadow-sm">
      <div className="max-w-[1920px] mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Left: Brand & Tagline */}
        <div className="flex items-center gap-3.5">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-talus-600 flex items-center justify-center shadow-md border border-talus-700">
              <Activity className="w-5 h-5 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold tracking-wider text-lg text-mine-text font-mono flex items-center gap-1.5">
                  TALUS
                  <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-talus-600/15 text-talus-600 border border-talus-600/30">
                    SIH26001
                  </span>
                </span>
                {/* Demo mode badge */}
                <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-mine-card text-[10px] font-medium text-mine-muted border border-mine-border">
                  <span className="w-1.5 h-1.5 rounded-full bg-risk-verylow animate-pulse"></span>
                  OFFLINE DEMO · Gangtok Corridor Prototype
                </span>
              </div>
              <p className="text-[11px] text-mine-muted font-medium">
                North-Eastern Region Landslide Early Warning & Decision Support (MDoNER)
              </p>
            </div>
          </div>
        </div>

        {/* Center: Location + Command Actions (Simulation, Routing, Field Reports) */}
        <div className="flex items-center gap-2 flex-wrap">
          <LocationSelector />
          {/* What-If Simulator Button */}
          <button
            onClick={() => setIsWhatIfOpen(true)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              activeSimulation
                ? 'bg-risk-moderate/20 text-mine-text border-risk-moderate shadow-md animate-pulse'
                : 'bg-mine-card hover:bg-mine-dark text-mine-text border-mine-border hover:border-talus-500'
            }`}
            title="Open geotechnical condition simulator"
          >
            <Sliders className="w-3.5 h-3.5 text-risk-moderate" />
            <span>What-If Simulator</span>
            {activeSimulation && (
              <span className="w-2 h-2 rounded-full bg-risk-moderate ml-0.5"></span>
            )}
          </button>

          {/* Safe Routing Button */}
          <button
            onClick={() => setIsRouteModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-mine-card hover:bg-mine-dark text-mine-text border border-mine-border hover:border-talus-500 transition-all"
            title="Calculate and compare safe routes avoiding at-risk road R2"
          >
            <Navigation className="w-3.5 h-3.5 text-risk-verylow" />
            <span>Safe Route (S1→S4)</span>
          </button>

          {/* Field Reports Modal Button */}
          <button
            onClick={() => setIsReportModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-mine-card hover:bg-mine-dark text-mine-text border border-mine-border hover:border-talus-500 transition-all relative"
            title="Submit field incident report or inspect officer verification queue"
          >
            <FileText className="w-3.5 h-3.5 text-talus-600" />
            <span>Field Reports</span>
            {reports && reports.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-talus-600 text-white text-[9px] font-bold">
                {reports.length}
              </span>
            )}
          </button>

          {/* Reset Baseline if active simulation */}
          {activeSimulation && (
            <button
              onClick={resetSimulation}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-risk-critical/15 hover:bg-risk-critical/25 text-risk-critical border border-risk-critical/30 transition-all"
              title="Reset simulated conditions back to pit baseline telemetry"
            >
              <RotateCcw className="w-3 h-3 text-risk-critical" />
              <span>Reset Sim</span>
            </button>
          )}
        </div>

        {/* Right: Active Alerts, Role Selector, Clock & Status */}
        <div className="flex items-center gap-3">
          {/* Active Alerts Drawer Trigger */}
          <button
            onClick={() => setIsAlertsDrawerOpen(true)}
            className="relative p-2 bg-mine-card hover:bg-mine-dark border border-mine-border hover:border-talus-500 rounded-lg text-mine-muted hover:text-mine-text transition-all group"
            title="View Active Risk Escalation Alerts"
          >
            <Bell className="w-4 h-4 group-hover:text-risk-moderate transition-colors" />
            {unacknowledgedAlertsCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-risk-critical text-white font-bold text-[10px] flex items-center justify-center ring-2 ring-mine-card animate-pulse">
                {unacknowledgedAlertsCount}
              </span>
            )}
          </button>

          {/* Role-Specific Perspective Selector */}
          <RoleSelector />

          {/* Corridor Telemetry & Clock */}
          <div className="hidden lg:flex flex-col items-end pl-2 border-l border-mine-border text-right font-mono">
            <div className="flex items-center gap-1.5 text-[11px] text-mine-text">
              <Clock className="w-3 h-3 text-mine-muted" />
              <span>{currentTime.toLocaleTimeString('en-US', { hour12: false })}</span>
              <span className="text-[9px] text-mine-muted font-sans">IST</span>
            </div>
            <div className="flex items-center gap-1 text-[10px] text-risk-verylow font-sans">
              <span className="w-1.5 h-1.5 rounded-full bg-risk-verylow animate-pulse"></span>
              IMD Gangtok Feed Live
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
