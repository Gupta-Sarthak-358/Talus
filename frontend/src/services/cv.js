import { apiRequest, isLiveApiEnabled, simulateLatency } from './api';
import { CV_SAMPLE_ANALYSES } from '../data/mockData';

/**
 * Fetch geotechnical CV crack analysis results
 * Contract: GET /api/cv/analysis/{zone_id}
 */
export async function getCvCrackAnalysis(zoneId = 'B') {
  if (isLiveApiEnabled()) {
    return apiRequest(`/cv/analysis/${zoneId}`);
  }

  await simulateLatency(300);

  const sample = CV_SAMPLE_ANALYSES.find((s) => s.zoneId === zoneId) || CV_SAMPLE_ANALYSES[0];
  return {
    status: 'success',
    analysis: sample,
  };
}
