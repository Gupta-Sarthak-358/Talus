import React, { useState, useEffect } from 'react';
import { useMineContext } from '../../context/MineContext';
import { WHAT_IF_PRESETS } from '../../data/mockData';
import SimulationDiffCard from './SimulationDiffCard';
import { Sliders, X, Sparkles, RotateCcw, Play, CloudRain, Activity, GitCommit, Layers } from 'lucide-react';

export default function WhatIfDrawer() {
  const {
    isWhatIfOpen,
    setIsWhatIfOpen,
    zones,
    selectedZoneId,
    selectedZoneData,
    runSimulation,
    resetSimulation,
    activeSimulation,
    simulationLoading,
  } = useMineContext();

  const [targetZoneId, setTargetZoneId] = useState(selectedZoneId || 'B');
  const [params, setParams] = useState({
    rainfall_24h: 88,
    blast_vibration: 34,
    crack_density: 16,
    slope_angle: 64,
  });

  // Sync target zone with selected zone when drawer opens
  useEffect(() => {
    if (selectedZoneId) {
      setTargetZoneId(selectedZoneId);
      const z = zones.find((item) => item.id === selectedZoneId);
      if (z && z.telemetry) {
        setParams({
          rainfall_24h: z.telemetry.rainfall_24h || 50,
          blast_vibration: z.telemetry.blast_vibration_ppv || 15,
          crack_density: z.telemetry.crack_density || 8,
          slope_angle: z.telemetry.slope_angle || 50,
        });
      }
    }
  }, [selectedZoneId, zones]);

  if (!isWhatIfOpen) return null;

  const handleApplyPreset = (preset) => {
    setParams(preset.values);
  };

  const handleRun = async () => {
    await runSimulation({
      zone_id: targetZoneId,
      ...params,
    });
  };

  const targetZone = zones.find((z) => z.id === targetZoneId) || selectedZoneData;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-opacity">
      <div className="w-full max-w-lg bg-mine-card border-l border-mine-border h-full flex flex-col shadow-2xl overflow-hidden animate-in slide-in-from-right duration-300">
        {/* Drawer Header */}
        <div className="p-4 bg-mine-darker border-b border-mine-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
              <Sliders className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">What-If Condition Simulator</h3>
              <p className="text-[11px] text-slate-400">
                Simulate geotechnical and weather changes in real time
              </p>
            </div>
          </div>

          <button
            onClick={() => setIsWhatIfOpen(false)}
            className="p-1.5 rounded-lg hover:bg-mine-border text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 p-5 space-y-5 overflow-y-auto">
          {/* Target Zone Selection */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">Target Mine Sector:</label>
            <select
              value={targetZoneId}
              onChange={(e) => setTargetZoneId(e.target.value)}
              className="w-full bg-mine-darker border border-mine-border rounded-lg px-3 py-2 text-xs font-semibold text-slate-100 focus:outline-none focus:border-talus-500"
            >
              {zones.map((z) => (
                <option key={z.id} value={z.id}>
                  {z.name} (Current Risk: {z.risk_score})
                </option>
              ))}
            </select>
          </div>

          {/* Quick Scenario Presets */}
          <div className="space-y-2">
            <div className="text-xs font-semibold text-slate-300 flex items-center justify-between">
              <span>Quick Demo Presets:</span>
              <span className="text-[10px] text-talus-400">Click to load</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {WHAT_IF_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => handleApplyPreset(preset)}
                  className="p-2 bg-mine-darker hover:bg-mine-dark border border-mine-border hover:border-talus-500/50 rounded-lg text-left transition-all"
                >
                  <div className="text-[11px] font-bold text-slate-200">{preset.name}</div>
                  <div className="text-[10px] text-slate-400 line-clamp-1 mt-0.5">{preset.expectedImpact}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Parameter Sliders */}
          <div className="space-y-4 bg-mine-darker/60 p-4 rounded-xl border border-mine-border/80">
            {/* 1. Rainfall Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 flex items-center gap-1.5">
                  <CloudRain className="w-3.5 h-3.5 text-blue-400" />
                  24h Cumulative Rainfall:
                </span>
                <span className="font-mono font-bold text-white">{params.rainfall_24h} mm</span>
              </div>
              <input
                type="range"
                min="0"
                max="120"
                value={params.rainfall_24h}
                onChange={(e) => setParams({ ...params, rainfall_24h: Number(e.target.value) })}
                className="w-full accent-talus-500 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-slate-500 font-mono">
                <span>0 mm (Dry)</span>
                <span>60 mm (Moderate)</span>
                <span>120 mm (Extreme Monsoon)</span>
              </div>
            </div>

            {/* 2. Blast Vibration PPV */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-orange-400" />
                  Blast Vibration (PPV):
                </span>
                <span className="font-mono font-bold text-white">{params.blast_vibration} mm/s</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                value={params.blast_vibration}
                onChange={(e) => setParams({ ...params, blast_vibration: Number(e.target.value) })}
                className="w-full accent-talus-500 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-slate-500 font-mono">
                <span>0 mm/s (None)</span>
                <span>25 mm/s (Controlled)</span>
                <span>50 mm/s (High Blast Wave)</span>
              </div>
            </div>

            {/* 3. Crack Density */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 flex items-center gap-1.5">
                  <GitCommit className="w-3.5 h-3.5 text-red-400" />
                  Tension Crack Density:
                </span>
                <span className="font-mono font-bold text-white">{params.crack_density} /m²</span>
              </div>
              <input
                type="range"
                min="0"
                max="25"
                value={params.crack_density}
                onChange={(e) => setParams({ ...params, crack_density: Number(e.target.value) })}
                className="w-full accent-talus-500 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-slate-500 font-mono">
                <span>0 /m² (Intact)</span>
                <span>12 /m² (Joint Sets)</span>
                <span>25 /m² (Severe Fracturing)</span>
              </div>
            </div>

            {/* 4. Slope Angle */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-talus-400" />
                  Highwall Slope Angle:
                </span>
                <span className="font-mono font-bold text-white">{params.slope_angle}°</span>
              </div>
              <input
                type="range"
                min="30"
                max="75"
                value={params.slope_angle}
                onChange={(e) => setParams({ ...params, slope_angle: Number(e.target.value) })}
                className="w-full accent-talus-500 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-slate-500 font-mono">
                <span>30° (Gentle)</span>
                <span>55° (Standard Bench)</span>
                <span>75° (Steep Highwall)</span>
              </div>
            </div>
          </div>

          {/* Action Triggers */}
          <div className="flex gap-2">
            <button
              onClick={handleRun}
              disabled={simulationLoading}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-talus-600 to-talus-500 hover:from-talus-500 hover:to-talus-400 text-white rounded-lg text-xs font-bold transition-all shadow-lg shadow-talus-500/25 disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              <span>{simulationLoading ? 'Inferring ML Risk Shift...' : 'Run What-If Simulation'}</span>
            </button>

            {activeSimulation && (
              <button
                onClick={resetSimulation}
                className="px-3 py-2.5 bg-mine-border hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-colors"
                title="Reset back to pit baseline telemetry"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Simulation Output Card */}
          {activeSimulation && (
            <SimulationDiffCard
              simulationResult={activeSimulation}
              baselineZone={targetZone}
            />
          )}
        </div>
      </div>
    </div>
  );
}
