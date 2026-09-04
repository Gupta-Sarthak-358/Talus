import React, { useState, useEffect } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import { WHAT_IF_PRESETS } from '../../data/constants';
import SimulationDiffCard from './SimulationDiffCard';
import { runCausalWhatIf, getScenarioTemplates } from '../../services/scenario';
import { Sliders, X, Sparkles, RotateCcw, Play, CloudRain, Activity, GitCommit, Layers, FlaskConical, Clock } from 'lucide-react';

const CAUSAL_KINDS = ['rainfall_storm', 'prolonged_rain', 'blast_surge', 'combined', 'historical_rain'];

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
    t,
  } = useTalusContext();

  const [targetZoneId, setTargetZoneId] = useState(selectedZoneId || 'S3');
  const [params, setParams] = useState({
    rainfall_24h: 132,
    blast_vibration: 10,
    crack_density: 0.5,
    slope_angle: 28,
  });

  // Sync target zone with selected zone when drawer opens
  useEffect(() => {
    if (selectedZoneId) {
      setTargetZoneId(selectedZoneId);
      const z = zones.find((item) => item.id === selectedZoneId);
      if (z && z.telemetry) {
        setParams({
          rainfall_24h: z.telemetry.rainfall_24h || 132,
          blast_vibration: z.telemetry.blast_vibration_ppv || 10,
          crack_density: z.telemetry.crack_density || 0.5,
          slope_angle: z.telemetry.slope_angle || 28,
        });
      }
    }
  }, [selectedZoneId, zones]);

  // Causal mode state (hooks MUST run on every render -- keep above early return)
  const [mode, setMode] = useState('ml'); // 'ml' | 'causal'
  const [causalLoading, setCausalLoading] = useState(false);
  const [causalResult, setCausalResult] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [causalForm, setCausalForm] = useState({
    kind: 'rainfall_storm',
    start_day: 0,
    duration_days: 7,
    params: { template_id: 'monga-mdl' },
    horizon_days: 14,
  });
  const [hoveredPreset, setHoveredPreset] = useState(null);

  useEffect(() => {
    getScenarioTemplates().then((r) => setTemplates(r.templates || [])).catch(() => {});
  }, []);

  if (!isWhatIfOpen) return null;

  const handleApplyPreset = (preset) => {
    setParams(preset.values);
    if (preset.targetZone) {
      setTargetZoneId(preset.targetZone);
    }
  };

  const handleRunCausal = async () => {
    setCausalLoading(true);
    setCausalResult(null);
    try {
      const res = await runCausalWhatIf({ zone_id: targetZoneId, ...causalForm });
      setCausalResult(res);
    } catch (err) {
      setCausalResult({ error: String(err.message || err) });
    } finally {
      setCausalLoading(false);
    }
  };

  const handleRun = async () => {
    await runSimulation({
      zone_id: targetZoneId,
      ...params,
    });
  };

  const targetZone = zones.find((z) => z.id === targetZoneId) || selectedZoneData;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-sm transition-opacity">
      <div className="w-full max-w-lg bg-mine-card border-l border-mine-border h-full flex flex-col shadow-2xl overflow-hidden animate-in slide-in-from-right duration-300">
        {/* Drawer Header */}
        <div className="p-4 bg-mine-darker border-b border-mine-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
              <Sliders className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-mine-text">{t('sim.title')}</h3>
              <p className="text-[11px] text-mine-muted">
                {t('sim.subtitle')}
              </p>
            </div>
          </div>

          <button
            onClick={() => setIsWhatIfOpen(false)}
            className="p-1.5 rounded-lg hover:bg-mine-border text-mine-muted hover:text-mine-text transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 p-5 space-y-5 overflow-y-auto">
          {/* Target Zone Selection */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-mine-text">{t('sim.targetSector')}</label>
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

          {/* Mode toggle: the two What-If paths are fundamentally different */}
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => setMode('ml')}
              className={`py-2 rounded-lg text-[11px] font-bold transition-colors ${mode === 'ml' ? 'bg-talus-600 text-mine-text' : 'bg-mine-border text-mine-muted hover:text-mine-text'}`}
            >
              {t('sim.mlCounterfactual')}
            </button>
            <button
              onClick={() => setMode('causal')}
              className={`py-2 rounded-lg text-[11px] font-bold transition-colors ${mode === 'causal' ? 'bg-emerald-600 text-mine-text' : 'bg-mine-border text-mine-muted hover:text-mine-text'}`}
            >
              {t('sim.causalPhysics')}
            </button>
          </div>
          <p className="text-[10px] text-mine-muted leading-relaxed">
            {mode === 'ml'
              ? t('sim.mlDesc')
              : t('sim.causalDesc')}
          </p>

          {mode === 'causal' && (
            <>
              <div className="space-y-3">
                <div>
                  <label className="text-[10px] font-semibold text-mine-muted uppercase tracking-wider">
                    {t('sim.template')}
                  </label>
                  <select
                    value={causalForm.params?.template_id || 'monga-mdl'}
                    onChange={(e) => setCausalForm({
                      ...causalForm,
                      params: { ...causalForm.params, template_id: e.target.value },
                    })}
                    className="w-full mt-1 bg-mine-darker border border-mine-border rounded-lg px-2.5 py-1.5 text-xs text-mine-text focus:outline-none focus:border-talus-500"
                  >
                    {templates.map((t) => (
                      <option key={t.template_id || t.id} value={t.template_id || t.id}>
                        {t.name || t.template_id || t.id} — {t.formula || t.demo_effect || ''}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="text-[9px] text-mine-muted uppercase">{t('sim.start')}</label>
                    <input type="number" min="0" value={causalForm.start_day}
                      onChange={(e) => setCausalForm({ ...causalForm, start_day: Number(e.target.value) })}
                      className="w-full mt-1 bg-mine-darker border border-mine-border rounded-lg px-2 py-1 text-xs text-mine-text" />
                  </div>
                  <div>
                    <label className="text-[9px] text-mine-muted uppercase">{t('sim.duration')}</label>
                    <input type="number" min="1" value={causalForm.duration_days}
                      onChange={(e) => setCausalForm({ ...causalForm, duration_days: Number(e.target.value) })}
                      className="w-full mt-1 bg-mine-darker border border-mine-border rounded-lg px-2 py-1 text-xs text-mine-text" />
                  </div>
                  <div>
                    <label className="text-[9px] text-mine-muted uppercase">{t('sim.horizon')}</label>
                    <input type="number" min="30" max="1500" step="30" value={causalForm.horizon_days}
                      onChange={(e) => setCausalForm({ ...causalForm, horizon_days: Number(e.target.value) })}
                      className="w-full mt-1 bg-mine-darker border border-mine-border rounded-lg px-2 py-1 text-xs text-mine-text" />
                  </div>
                </div>

                <button
                  onClick={handleRunCausal}
                  disabled={causalLoading}
                  className="w-full flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-mine-text rounded-lg text-xs font-bold transition-all shadow-lg shadow-emerald-500/25 disabled:opacity-50"
                >
                  <FlaskConical className="w-4 h-4" />
                  <span>{causalLoading ? t('sim.propagating') : t('sim.run_causal')}</span>
                </button>
              </div>

              {causalResult?.error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-[11px] text-red-300">
                  {causalResult.error}
                </div>
              )}
              {causalResult?.summary && (
                <div className="space-y-3">
                  <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                    <div className="flex items-center gap-2 mb-2">
                      <Clock className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-[11px] font-bold text-mine-text">{t('sim.traj')}</span>
                      <span className="ml-auto text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                        gen v{causalResult.generator_version}
                      </span>
                    </div>
                    <p className="text-[11px] text-mine-text leading-relaxed mb-2">
                      {causalResult.summary.open_crack_branch_fired
                        ? 'Repeated extreme wetting degraded crack strength past its threshold — stability now diverges from baseline and recovers slowly.'
                        : 'Scenario response contained within this horizon: no strength-threshold branch was triggered.'}
                      {' '}Max wetting memory reached {causalResult.summary.max_groundwater_proxy_mm} mm.
                    </p>
                    <details className="text-[11px]">
                      <summary className="cursor-pointer text-mine-muted hover:text-mine-text select-none">
                        {t('sim.advanced')}
                      </summary>
                      <div className="grid grid-cols-2 gap-x-3 gap-y-1 mt-2">
                      <span className="text-mine-muted">Min FoS (baseline → scenario)</span>
                      <span className="text-right font-mono text-mine-text">
                        {causalResult.summary.baseline_min_fos} → {causalResult.summary.scenario_min_fos}
                      </span>
                      <span className="text-mine-muted">FoS divergence</span>
                      <span className={`text-right font-mono font-bold ${causalResult.summary.fos_divergence_min < -0.05 ? 'text-red-400' : 'text-mine-text'}`}>
                        {causalResult.summary.fos_divergence_min} @ day {causalResult.summary.divergence_day}
                      </span>
                      <span className="text-mine-muted">Days diverging &gt;0.01</span>
                      <span className="text-right font-mono text-mine-text">{causalResult.summary.days_diverging_gt_001}</span>
                      <span className="text-mine-muted">Open-crack branch fired</span>
                      <span className={`text-right font-mono ${causalResult.summary.open_crack_branch_fired ? 'text-red-400' : 'text-mine-muted'}`}>
                        {causalResult.summary.open_crack_branch_fired ? 'YES' : 'no'}
                      </span>
                      <span className="text-mine-muted">Max groundwater proxy</span>
                      <span className="text-right font-mono text-mine-text">{causalResult.summary.max_groundwater_proxy_mm} mm</span>
                      <span className="text-mine-muted">First response day</span>
                      <span className="text-right font-mono text-mine-text">{causalResult.summary.first_response_day ?? '-'}</span>
                    </div>
                    </details>
                  </div>

                  {causalResult.provenance && (
                    <div className="p-2.5 rounded-lg bg-mine-darker border border-mine-border text-[10px] text-mine-muted">
                      <span className="font-semibold text-mine-text">{t('sim.provenance')}</span>{' '}
                      {causalResult.provenance.template_id} [{causalResult.provenance.imd_window?.[0]} … {causalResult.provenance.imd_window?.[1]}]
                      {' · '}{causalResult.provenance.window_total_mm} mm total · max day {causalResult.provenance.window_max_day_mm} mm
                      <div className="text-mine-muted mt-0.5">{causalResult.provenance.source}</div>
                    </div>
                  )}

                  {(causalResult.evidence_timeline || []).length > 0 && (
                    <div>
                      <div className="text-[10px] font-semibold text-mine-muted uppercase tracking-wider mb-1.5">
                        {t('sim.evidence_timeline')}
                      </div>
                      <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                        {causalResult.evidence_timeline.map((ev, i) => (
                          <div key={i} className="p-2 rounded-lg bg-mine-darker border border-mine-border">
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="font-mono text-mine-text">{t('sim.day')} {ev.day}</span>
                              <span className="font-mono">
                                <span className="text-mine-muted">{ev.score_from}</span>
                                <span className="text-mine-muted mx-1">→</span>
                                <span className={ev.score_to > ev.score_from ? 'text-red-400 font-bold' : 'text-mine-text font-bold'}>
                                  {ev.score_to}
                                </span>
                              </span>
                            </div>
                            <ul className="mt-1 space-y-0.5">
                              {ev.causes.map((cause, j) => (
                                <li key={j} className="text-[10px] text-mine-text font-medium">↳ {cause}</li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {mode === 'ml' && (<>
          {/* Quick Scenario Presets */}
          <div className="space-y-2">
            <div className="text-xs font-semibold text-mine-text flex items-center justify-between">
              <span>{t('sim.presets')}</span>
              <span className="text-[10px] text-talus-400">{t('sim.presets_hint')}</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {WHAT_IF_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => { handleApplyPreset(preset); setHoveredPreset(preset); }}
                  onMouseEnter={() => setHoveredPreset(preset)}
                  onFocus={() => setHoveredPreset(preset)}
                  className={`p-2 border rounded-lg text-left transition-all ${
                    hoveredPreset?.id === preset.id
                      ? 'bg-mine-dark border-talus-500/60'
                      : 'bg-mine-darker hover:bg-mine-dark border-mine-border hover:border-talus-500/50'
                  }`}
                >
                  <div className="text-[11px] font-bold text-mine-text">{preset.name}</div>
                </button>
              ))}
            </div>

            {/* Hover detail card: full description without truncation */}
            {hoveredPreset && (
              <div className="p-3 bg-mine-darker border border-talus-500/40 rounded-lg space-y-1.5">
                <div className="text-[11px] font-bold text-mine-text">{hoveredPreset.name}</div>
                <p className="text-[10px] text-mine-text leading-relaxed">{hoveredPreset.description}</p>
                <div className="text-[10px] text-mine-muted leading-relaxed">
                  <span className="font-semibold text-mine-muted">{t('sim.inputs_applied')} </span>
                  {Object.entries(hoveredPreset.values).map(([k, v]) => `${k} = ${v}`).join(' · ')}
                </div>
              </div>
            )}
          </div>

          {/* Interactive Parameter Sliders */}
          <div className="space-y-4 bg-mine-darker/60 p-4 rounded-xl border border-mine-border/80">
            {/* 1. Rainfall Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-mine-text flex items-center gap-1.5">
                  <CloudRain className="w-3.5 h-3.5 text-blue-400" />
                  {t('sim.rainfall')}
                </span>
                <span className="font-mono font-bold text-mine-text">{params.rainfall_24h} mm</span>
              </div>
              <input
                type="range"
                min="0"
                max="120"
                value={params.rainfall_24h}
                onChange={(e) => setParams({ ...params, rainfall_24h: Number(e.target.value) })}
                className="w-full accent-talus-500 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-mine-muted font-mono">
                <span>0 mm (Dry)</span>
                <span>60 mm (Moderate)</span>
                <span>120 mm (Extreme Monsoon)</span>
              </div>
            </div>

            {/* 2. Vibration Proxy (PPV) — kept for model compat, treated as ground-motion proxy for NER */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-mine-text flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-orange-400" />
                  {t('sim.vibration')}
                </span>
                <span className="font-mono font-bold text-mine-text">{params.blast_vibration} mm/s</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                value={params.blast_vibration}
                onChange={(e) => setParams({ ...params, blast_vibration: Number(e.target.value) })}
                className="w-full accent-talus-500 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-mine-muted font-mono">
                <span>0 mm/s (Stable)</span>
                <span>25 mm/s (Elevated)</span>
                <span>50 mm/s (Severe)</span>
              </div>
            </div>

            {/* 3. Crack Density */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-mine-text flex items-center gap-1.5">
                  <GitCommit className="w-3.5 h-3.5 text-red-400" />
                  {t('sim.crack')}
                </span>
                <span className="font-mono font-bold text-mine-text">{params.crack_density} /m²</span>
              </div>
              <input
                type="range"
                min="0"
                max="2.5" step="0.05"
                value={params.crack_density}
                onChange={(e) => setParams({ ...params, crack_density: Number(e.target.value) })}
                className="w-full accent-talus-500 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-mine-muted font-mono">
                <span>0 /m² (Intact)</span>
                <span>12 /m² (Joint Sets)</span>
                <span>25 /m² (Severe Fracturing)</span>
              </div>
            </div>

            {/* 4. Slope Angle */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-mine-text flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-talus-400" />
                  {t('sim.slopeAngle')}
                </span>
                <span className="font-mono font-bold text-mine-text">{params.slope_angle}°</span>
              </div>
              <input
                type="range"
                min="30"
                max="75"
                value={params.slope_angle}
                onChange={(e) => setParams({ ...params, slope_angle: Number(e.target.value) })}
                className="w-full accent-talus-500 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-mine-muted font-mono">
                <span>30° (Gentle)</span>
                <span>45° (Typical NER Cut)</span>
                <span>75° (Steep Scarp)</span>
              </div>
            </div>
          </div>

          {/* Action Triggers */}
          <div className="flex gap-2">
            <button
              onClick={handleRun}
              disabled={simulationLoading}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-talus-600 to-talus-500 hover:from-talus-500 hover:to-talus-400 text-mine-text rounded-lg text-xs font-bold transition-all shadow-lg shadow-talus-500/25 disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              <span>{simulationLoading ? t('sim.inferring') : t('sim.run')}</span>
            </button>

            {activeSimulation && (
              <button
                onClick={resetSimulation}
                className="px-3 py-2.5 bg-mine-border hover:bg-slate-700 text-mine-text rounded-lg text-xs font-medium transition-colors"
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
          </>)}
        </div>
      </div>
    </div>
  );
}
