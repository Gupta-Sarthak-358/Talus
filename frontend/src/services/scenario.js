import { apiRequest, isLiveApiEnabled } from './api';

/**
 * Causal physics What-If (Scenario Engine v1.5).
 * Modifies CAUSES (rain realization / blast schedule); the frozen generator
 * v1.4.0 chain propagates them into a day-by-day FoS/score trajectory.
 * Distinct from the ML counterfactual in simulateConditions().
 */

export async function getScenarioTemplates() {
  if (!isLiveApiEnabled()) {
    return { templates: [
      { template_id: 'dec_1902', imd_window: ['1902-12-01', '1902-12-31'], window_total_mm: 1088.2, window_max_day_mm: 297.6, source: 'IMD 0.25deg Neyveli grid 11.5N 79.5E' },
      { template_id: 'apr_1931', imd_window: ['1931-04-01', '1931-04-30'], window_total_mm: 430.0, window_max_day_mm: 333.0, source: 'IMD 0.25deg Neyveli grid 11.5N 79.5E' },
      { template_id: 'nov_2015', imd_window: ['2015-11-01', '2015-11-30'], window_total_mm: 974.0, window_max_day_mm: 327.0, source: 'IMD 0.25deg Neyveli grid 11.5N 79.5E' },
      { template_id: 'dec_1996', imd_window: ['1996-12-01', '1996-12-31'], window_total_mm: 805.0, window_max_day_mm: 156.0, source: 'IMD 0.25deg Neyveli grid 11.5N 79.5E' },
    ] };
  }
  return apiRequest('/simulation/templates');
}

export async function runCausalWhatIf({
  zone_id = 'C',
  kind = 'historical_rain',
  start_day = 550,
  duration_days = 31,
  params = { template_id: 'dec_1902' },
  horizon_days = 1095,
  seed = 42,
}) {
  if (!isLiveApiEnabled()) {
    // Offline fallback mirrors the frozen validation run (deterministic).
    await import('./api').then((m) => m.simulateLatency(400));
    return {
      zone_id, scenario_name: `offline_${kind}`, mode: 'causal_physics',
      generator_version: '1.4.0',
      summary: {
        baseline_min_fos: 1.739, scenario_min_fos: 1.739, delta_min_fos: 0.0,
        fos_divergence_min: -0.761, divergence_day: 553, days_diverging_gt_001: 51,
        baseline_peak_instability: 38.1, scenario_peak_instability: 38.1,
        delta_peak_instability: 0.0,
        baseline_days_high_or_critical: 0, scenario_days_high_or_critical: 0,
        first_response_day: 550, worst_day: 299, worst_day_risk: 'very_low',
        max_groundwater_proxy_mm: 840.8, open_crack_branch_fired: true,
      },
      provenance: {
        template_id: params.template_id || 'dec_1902',
        imd_window: ['1902-12-01', '1902-12-31'], window_total_mm: 1088.2,
        window_max_day_mm: 297.6, source: 'IMD 0.25deg Neyveli grid 11.5N 79.5E',
      },
      evidence_timeline: [
        { day: 550, score_from: 0.0, score_to: 35.4, fos: 1.74,
          causes: ['historical storm replay begins (Dec-1902 profile)'] },
        { day: 553, score_from: 35.4, score_to: 36.6, fos: 1.74,
          causes: ['heavy rainfall (+298 mm/24h)', 'groundwater proxy rose (+180 mm)',
                   'cracks became water-filled'] },
      ],
      trajectory: [],
    };
  }
  return apiRequest('/simulation/causal-what-if', {
    method: 'POST',
    body: JSON.stringify({ zone_id, kind, start_day, duration_days, params, horizon_days, seed }),
  });
}