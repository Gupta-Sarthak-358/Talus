import { apiRequest } from './api';

/**
 * Alerts — LIVE SIH26001 (real /api/alerts/dispatch, en/hi/ne fixture from backend).
 */

export async function dispatchAlerts({ channel = 'app', lang = 'en', zone_id = null, message = null } = {}) {
  const qs = new URLSearchParams({ channel, lang, ...(zone_id ? { zone_id } : {}), ...(message ? { message } : {}) }).toString();
  const res = await apiRequest(`/alerts/dispatch?${qs}`, { method: 'POST' });
  return res;
}

export async function getDispatchLog(limit = 20) {
  return apiRequest(`/alerts/dispatch/log?limit=${limit}`);
}

export async function getHealth() {
  const base = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/api\/?$/, '');
  try {
    const r = await fetch(`${base}/health`);
    if (r.ok) return r.json();
    return null;
  } catch { return null; }
}
