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

export async function simulateConditions({ zone_id = 'S3', ...params }) {
  if (isLiveApiEnabled()) {
    try {
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
    } catch (e) {
      console.warn('Live what-if failed, falling back to offline fixture:', e);
    }
  }

  // Offline fixture mode per SCAFFOLD_CONTRACT_SEPT5.md §2 & forecast.json:
  // S3: 66 -> 74, delta = 8
  await simulateLatency(300);
  const baselineScore = zone_id === 'S3' ? 66 : zone_id === 'S1' ? 89 : zone_id === 'S2' ? 78 : 52;
  const baselineBand = zone_id === 'S3' ? 'MODERATE' : zone_id === 'S1' ? 'CRITICAL' : zone_id === 'S2' ? 'HIGH' : 'LOW';
  
  // When rainfall is elevated or S3 is selected
  const delta = zone_id === 'S3' ? 8 : params.rainfall_24h > 90 ? 8 : 4;
  const simulatedScore = baselineScore + delta;
  const simulatedBand = simulatedScore >= 85 ? 'CRITICAL' : simulatedScore >= 75 ? 'HIGH' : simulatedScore >= 65 ? 'MODERATE' : 'LOW';

  return {
    risk_score: simulatedScore,
    risk_band: simulatedBand,
    confidence: 65,
    baselineScore,
    baselineBand,
    shap: [
      { feature: 'rainfall_24h_mm (overridden to ' + (params.rainfall_24h || 132) + ' mm)', value: delta },
      { feature: 'soil_moisture (proxy)', value: 3.5 },
    ],
    trend: {
      direction: 'rising',
      rapid: true,
      history: [
        { time: 'Day 0', risk: baselineScore, label: 'Observed' },
        { time: 'Simulated', risk: simulatedScore, label: 'What-If Peak' },
      ],
    },
    explanationText: `ML counterfactual: baseline ${baselineScore} -> ${simulatedScore} (${simulatedBand}). Delta +${delta}. Single-feature override.`,
    delta,
    isEscalated: delta > 0,
    zone_id,
    inputs: { rainfall_24h: params.rainfall_24h },
    mode: 'ml_counterfactual',
    caveat: 'Counterfactual only — single-feature override breaks correlations. Causal questions use the threshold engine.',
  };
}

export { runCausalWhatIf, getScenarioTemplates } from './scenario';