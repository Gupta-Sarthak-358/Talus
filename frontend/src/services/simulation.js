import { apiRequest, isLiveApiEnabled, simulateLatency } from './api';
import { MOCK_ZONES } from '../data/mockData';

/**
 * Simulate geotechnical and meteorological conditions for a mine zone
 * Contract: POST /api/simulate
 * Request: { zone_id, rainfall_24h, blast_vibration, crack_density, slope_angle }
 */
export async function simulateConditions({
  zone_id = 'B',
  rainfall_24h = 80,
  blast_vibration = 25,
  crack_density = 12,
  slope_angle = 60,
}) {
  if (isLiveApiEnabled()) {
    return apiRequest('/simulate', {
      method: 'POST',
      body: JSON.stringify({
        zone_id,
        rainfall_24h,
        blast_vibration,
        crack_density,
        slope_angle,
      }),
    });
  }

  // Simulated ML inference latency
  await simulateLatency(350);

  const baselineZone = MOCK_ZONES.find((z) => z.id === zone_id) || MOCK_ZONES[1];

  // Model-agnostic mock feature calculation (simulating Random Forest output with non-linear factors)
  // Baseline risk weight formula for demonstration
  const rainScore = Math.min(30, (rainfall_24h / 100) * 28);
  const blastScore = Math.min(25, (blast_vibration / 50) * 24);
  const crackScore = Math.min(30, (crack_density / 20) * 26);
  const slopeScore = Math.min(25, ((slope_angle - 30) / 45) * 22);

  const calculatedRisk = Math.min(
    98,
    Math.max(10, Math.round(12 + rainScore + blastScore + crackScore + slopeScore))
  );

  let riskBand = 'LOW';
  if (calculatedRisk <= 20) riskBand = 'VERY_LOW';
  else if (calculatedRisk <= 40) riskBand = 'LOW';
  else if (calculatedRisk <= 65) riskBand = 'MODERATE';
  else if (calculatedRisk <= 84) riskBand = 'HIGH';
  else riskBand = 'CRITICAL';

  // Dynamic SHAP calculations matching simulated values
  const simulatedShap = [
    {
      feature: `Slope Angle (${Math.round(slope_angle)}°)`,
      value: Math.round(slopeScore),
      rawValue: `${Math.round(slope_angle)}°`,
      description: slope_angle > 55 ? 'Over-steepened highwall' : 'Stable bench geometry',
    },
    {
      feature: `Crack Density (${crack_density.toFixed(1)}/m²)`,
      value: Math.round(crackScore),
      rawValue: `${crack_density.toFixed(1)} /m²`,
      description: crack_density > 10 ? 'Severe tension cracks propagating' : 'Minor hairline joints',
    },
    {
      feature: `Rainfall 24h (${Math.round(rainfall_24h)}mm)`,
      value: Math.round(rainScore),
      rawValue: `${Math.round(rainfall_24h)} mm`,
      description: rainfall_24h > 60 ? 'Severe saturation & pore pressure' : 'Normal surface drainage',
    },
    {
      feature: `Blast Vibration (${blast_vibration.toFixed(1)} mm/s)`,
      value: Math.round(blastScore),
      rawValue: `${blast_vibration.toFixed(1)} mm/s`,
      description: blast_vibration > 25 ? 'High dynamic shear excitation' : 'Sub-critical blast wave',
    },
  ].sort((a, b) => b.value - a.value);

  // Confidence adjusted slightly based on input extremes
  const simulatedConfidence = Math.max(70, Math.min(95, Math.round(85 - (blast_vibration > 30 ? 6 : 0) - (crack_density > 15 ? 4 : 0))));

  const isEscalated = calculatedRisk > baselineZone.risk_score;
  const delta = calculatedRisk - baselineZone.risk_score;

  return {
    status: 'success',
    timestamp: new Date().toISOString(),
    zone_id,
    zone_name: baselineZone.name,
    simulated: true,
    risk_score: calculatedRisk,
    risk_band: riskBand,
    confidence: simulatedConfidence,
    delta: delta >= 0 ? `+${delta}` : `${delta}`,
    isEscalated,
    inputs: {
      rainfall_24h,
      blast_vibration,
      crack_density,
      slope_angle,
    },
    shap: simulatedShap,
    trend: {
      direction: delta > 5 ? 'rising' : delta < -5 ? 'falling' : 'stable',
      delta: delta >= 0 ? `+${delta} pts (Simulated)` : `${delta} pts (Simulated)`,
      badge: delta > 5 ? '↑ Rapid Escalation' : delta < -5 ? '↓ Stabilized' : 'Stable',
      history: [
        { time: '09:00', risk: baselineZone.trend.history[0].risk, label: '09:00 AM' },
        { time: '10:00', risk: baselineZone.trend.history[1].risk, label: '10:00 AM' },
        { time: '11:00', risk: baselineZone.trend.history[2].risk, label: '11:00 AM' },
        { time: '12:00', risk: baselineZone.trend.history[3].risk, label: '12:00 PM' },
        { time: 'Simulated', risk: calculatedRisk, label: 'Simulated Scenario' },
      ],
    },
    explanationText: delta > 0
      ? `Simulated risk increased by ${delta} points primarily due to ${simulatedShap[0].feature} (+${simulatedShap[0].value}) and ${simulatedShap[1].feature} (+${simulatedShap[1].value}).`
      : `Simulated conditions reduce risk by ${Math.abs(delta)} points below baseline.`,
  };
}
