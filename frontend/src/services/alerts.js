import { apiRequest } from './api';

/**
 * Alerts — LIVE SIH26001 (real /api/alerts/dispatch, en/hi/ne fixture from backend).
 */

export async function dispatchAlerts() {
  const res = await apiRequest('/alerts/dispatch', { method: 'POST' });
  return res;
}
