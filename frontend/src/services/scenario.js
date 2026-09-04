import { apiRequest } from './api';

/**
 * Causal threshold What-If — LIVE SIH26001 (real model + USGS/IMD/CCI).
 * Contract: GET /api/simulation/templates, POST /api/simulation/causal-what-if
 * Templates: monga-mdl (E=-11.10+0.62*D) + dahal-144 (>144 mm/day)
 */

export async function getScenarioTemplates() {
  const res = await apiRequest('/simulation/templates');
  return res;
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
  const res = await apiRequest('/simulation/causal-what-if', {
    method: 'POST',
    body: JSON.stringify({ zone_id, kind, start_day, duration_days, params, horizon_days, seed }),
  });
  return res;
}
