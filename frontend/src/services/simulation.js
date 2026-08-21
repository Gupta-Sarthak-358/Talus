import { apiRequest, isLiveApiEnabled, simulateLatency } from './api';

/**
 * ML counterfactual What-If: overrides observed features and re-predicts
 * with the frozen RF. Contract: POST /api/simulation/what-if
 * Body: { zone_id, overrides } in V1 feature units.
 *
 * NOTE: this answers "what would the MODEL predict if this input changed?"
 * For causal physics trajectories use scenario.js (runCausalWhatIf).
 */

const OVERRIDE_MAP = {
  rainfall_24h: 'rainfall_24h_mm',
  blast_vibration: 'blast_vibration_ppv_mms',
  crack_density: 'crack_density',
  slope_angle: 'slope_angle_deg',
};

function toOverrides(params) {
  const overrides = {};
  for (const [k, v] of Object.entries(params)) {
    const key = OVERRIDE_MAP[k] || k;
    overrides[key] = v;
  }
  return overrides;
}

function bandUpper(band) {
  return String(band || '').toUpperCase().replace(' ', '_');
}

async function fetchTrend(zone_id) {
  try {
    const t = await apiRequest(`/zones/${zone_id}/trend`);
    return {
      direction: t.rapid_increase ? 'rapidly_increasing' : 'rising',
      rapid: !!t.rapid_increase,
      history: (t.history || []).map((p) => ({ time: p.t, risk: p.risk_score, label: p.t })),
    };
  } catch {
    return null;
  }
}

export async function simulateConditions({ zone_id = 'B', ...params }) {
  if (!isLiveApiEnabled()) {
    // Offline fallback cannot produce real model outputs; report honestly.
    await simulateLatency(350);
    throw new Error(
      'ML what-if requires the live backend (set VITE_USE_LIVE_API=true). ' +
      'The frozen RF does not run in the browser.'
    );
  }
  const res = await apiRequest('/simulation/what-if', {
    method: 'POST',
    body: JSON.stringify({ zone_id, overrides: toOverrides(params) }),
  });
  const sim = res.simulated || {};
  const base = res.baseline || {};
  const trend = await fetchTrend(zone_id);
  const delta = res.delta ?? 0;
  return {
    risk_score: sim.risk_score,
    risk_band: bandUpper(sim.risk_band),
    confidence: Math.round((sim.confidence ?? 0) * 100),
    baselineScore: base.risk_score,
    baselineBand: bandUpper(base.risk_band),
    shap: (res.contributions || []).map((c) => ({
      feature: c.feature,
      value: c.shap_value,
    })),
    trend,
    explanationText:
      `ML counterfactual: baseline ${res.baseline?.risk_score} -> ` +
      `${sim.risk_score} (${sim.risk_band}). Delta ${res.delta}.`,
    delta,
    isEscalated: delta > 0,
    zone_id,
    // QuickStatsBar reads activeSimulation.inputs.rainfall_24h
    inputs: { rainfall_24h: params.rainfall_24h },
    mode: 'ml_counterfactual',
  };
}

export { runCausalWhatIf, getScenarioTemplates } from './scenario';