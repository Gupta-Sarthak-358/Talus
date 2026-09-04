/**
 * CV crack detection is a DEFERRED Tier-3 capability (decision recorded in
 * docs/CURRENT_SYSTEM.md). No model was trained; no endpoint exists. This
 * service reports that honestly instead of returning invented analyses.
 */

export async function getCvCrackAnalysis(zoneId = 'B') {
  return {
    status: 'deferred',
    deferred: true,
    message:
      'Computer-vision crack detection is a deferred Tier-3 capability. ' +
      'No model has been trained (generic road/wall crack imagery does not ' +
      'transfer to mine rock faces without mine-specific data). Current ' +
      'crack features come from the physics-based inspection sampler.',
    zoneId,
  };
}