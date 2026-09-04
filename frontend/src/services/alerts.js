import { apiRequest, isLiveApiEnabled, simulateLatency } from './api';
import { MOCK_MULTILINGUAL_ALERT } from '../data/mockData';

export async function dispatchAlerts() {
  if (isLiveApiEnabled()) {
    try {
      const res = await apiRequest('/alerts/dispatch', { method: 'POST' });
      return res;
    } catch (e) {
      console.warn('Live alert dispatch failed, falling back to fixture:', e);
    }
  }
  await simulateLatency(250);
  return MOCK_MULTILINGUAL_ALERT;
}
