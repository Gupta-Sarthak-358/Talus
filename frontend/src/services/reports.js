import { apiRequest } from './api';

/**
 * Reports — LIVE SIH26001 (real /api/reports + /api/reports/queue?status=).
 * No mock fallback on 422 (validation) — only on network failure the caller may locally queue.
 */

let sessionReports = [];

export async function getReportsQueue(status) {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  const res = await apiRequest(`/reports/queue${qs}`);
  return res.reports || [];
}

export async function submitReport(reportData) {
  const res = await apiRequest('/reports', {
    method: 'POST',
    body: JSON.stringify(reportData),
  });
  return res;
}
