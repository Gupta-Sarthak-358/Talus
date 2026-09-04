import { apiRequest } from './api';

/**
 * ML counterfactual What-If — LIVE SIH26001 (real NGEN + USGS/IMD/CCI/WorldCover).
 * Contract: POST /api/simulation/what-if
 * Body: { zone_id, overrides } — frozen RF on 14+1 features, 1528-row model.
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

export async function simulateConditions({ zone_id = 'S3', ...params }) {
  const res = await apiRequest('/simulation/what-if', {
    method: 'POST',
    body: JSON.stringify({ zone_id, overrides: toOverrides(params) }),
  });
  const sim = res.simulated || {};
  const base = res.baseline || {};
  const trend = await fetchTrend(zone_id);
  const delta = res.delta ?? (sim.risk_score - base.risk_score);
  return {
    risk_score: sim.risk_score,
    risk_band: bandUpper(sim.risk_band),
    confidence: Math.round((sim.confidence ?? 0.65) * (sim.confidence <= 1 ? 100 : 1)),
    baselineScore: base.risk_score,
    baselineBand: bandUpper(base.risk_band),
    shap: (res.contributions || []).map((c) => ({
      feature: c.feature,
      value: c.shap_value ?? c.shap,
    })),
    trend,
    explanationText:
      `ML counterfactual: baseline ${base.risk_score} -> ` +
      `${sim.risk_score} (${sim.risk_band}). Delta ${delta > 0 ? '+' : ''}${delta}.`,
    delta,
    isEscalated: delta > 0,
    zone_id,
    inputs: { rainfall_24h: params.rainfall_24h },
    mode: 'ml_counterfactual',
    caveat: 'Counterfactual only — single-feature override breaks correlations. Causal questions use the threshold engine.',
  };
}

export { runCausalWhatIf, getScenarioTemplates } from './scenario';
