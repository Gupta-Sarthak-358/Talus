import { apiRequest, isLiveApiEnabled, simulateLatency } from './api';

/**
 * Causal threshold / physics What-If (Scenario Engine v1.5).
 * Contract: GET /api/simulation/templates, POST /api/simulation/causal-what-if
 * Templates: monga-mdl + dahal-144
 * Replay saturation trajectory -> newly escalated S3 (66 -> 78 High)
 */

export const SCENARIO_TEMPLATES = [
  {
    template_id: 'monga-mdl',
    id: 'monga-mdl',
    name: 'Monga 2026 MDL curve',
    formula: 'E = -11.10 + 0.62*D (24<D<1440h)',
    demo_effect: 'S3 Moderate(66) -> High(78), S1 stays Critical',
    source: 'IMD Gangtok rainfall fixture + Monga 2026 empirical threshold',
    window_total_mm: 515.0,
    window_max_day_mm: 132.0,
  },
  {
    template_id: 'dahal-144',
    id: 'dahal-144',
    name: 'Dahal-Hasegawa',
    formula: '>144 mm/day -> high risk (Himalayas)',
    demo_effect: 'flags S1+S2 on peak day',
    source: 'Himalayan Empirical Landslide Threshold (Dahal & Hasegawa)',
    window_total_mm: 420.0,
    window_max_day_mm: 144.0,
  },
];

export async function getScenarioTemplates() {
  if (isLiveApiEnabled()) {
    try {
      const res = await apiRequest('/simulation/templates');
      if (res.templates && res.templates.length > 0) return res;
    } catch (e) {
      console.warn('Live templates fetch failed, using fixture templates:', e);
    }
  }
  return { templates: SCENARIO_TEMPLATES };
}

export async function runCausalWhatIf({
  zone_id = 'S3',
  kind = 'threshold_saturation',
  start_day = 0,
  duration_days = 7,
  params = { template_id: 'monga-mdl' },
  horizon_days = 14,
  seed = 42,
} = {}) {
  if (isLiveApiEnabled()) {
    try {
      const res = await apiRequest('/simulation/causal-what-if', {
        method: 'POST',
        body: JSON.stringify({ zone_id, kind, start_day, duration_days, params, horizon_days, seed }),
      });
      return res;
    } catch (e) {
      console.warn('Live causal what-if failed, using fixture:', e);
    }
  }

  await simulateLatency(350);
  const templateId = params.template_id || 'monga-mdl';
  const isMonga = templateId === 'monga-mdl';

  return {
    zone_id: zone_id || 'S3',
    scenario_name: templateId,
    mode: 'causal_physics',
    generator_version: '1.4.0',
    divergence_note: 'Saturation trajectory -> newly escalated S3 (fixture numbers, real model pending)',
    escalated_units: ['S3'],
    summary: {
      baseline_min_fos: 1.35,
      scenario_min_fos: 0.98,
      delta_min_fos: -0.37,
      fos_divergence_min: -0.37,
      divergence_day: 3,
      days_diverging_gt_001: 5,
      baseline_peak_instability: 66,
      scenario_peak_instability: 78,
      delta_peak_instability: 12,
      baseline_days_high_or_critical: 0,
      scenario_days_high_or_critical: 4,
      first_response_day: 0,
      worst_day: 3,
      worst_day_risk: 'High',
      max_groundwater_proxy_mm: 515.0,
      open_crack_branch_fired: true,
    },
    provenance: {
      template_id: templateId,
      source: isMonga ? 'Monga 2026 MDL curve — E = -11.10 + 0.62*D' : 'Dahal-Hasegawa >144 mm/day',
      window_total_mm: isMonga ? 515.0 : 420.0,
      window_max_day_mm: isMonga ? 132.0 : 144.0,
      divergence_note: 'Saturation trajectory -> newly escalated S3 (fixture numbers, real model pending)',
    },
    timeline: [
      { t: 'Day 0', cause: '7-day rain +120 mm accumulation', effect: 'soil moisture saturated' },
      { t: 'Day 3', cause: '24h rain 132 mm peak', effect: 'S3 66 -> 78 (High) threshold breach' },
    ],
    evidence_timeline: [
      {
        day: 0,
        score_from: 66,
        score_to: 69,
        fos: 1.25,
        causes: ['7-day rain accumulation +120 mm', 'pore pressure rises in mid-Tadong soil mantle'],
      },
      {
        day: 3,
        score_from: 69,
        score_to: 78,
        fos: 0.98,
        causes: ['24h peak rain reaches 132 mm', 'Monga MDL threshold exceeded (E > -11.10 + 0.62*D)', 'S3 newly escalated: Moderate (66) -> High (78)'],
      },
    ],
    trajectory: [],
  };
}