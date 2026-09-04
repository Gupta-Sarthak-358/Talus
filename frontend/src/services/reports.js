import { apiRequest, isLiveApiEnabled, simulateLatency } from './api';
import { MOCK_REPORTS } from '../data/mockData';

let sessionReports = [...MOCK_REPORTS];

export async function getReportsQueue(status) {
  if (isLiveApiEnabled()) {
    try {
      const qs = status ? `?status=${encodeURIComponent(status)}` : '';
      const res = await apiRequest(`/reports/queue${qs}`);
      return res.reports || sessionReports;
    } catch (e) {
      console.warn('Live reports queue failed, using local queue:', e);
    }
  }
  await simulateLatency(150);
  if (status) return sessionReports.filter((r) => r.status === status);
  return sessionReports;
}

export async function submitReport(reportData) {
  if (isLiveApiEnabled()) {
    const res = await apiRequest('/reports', {
      method: 'POST',
      body: JSON.stringify(reportData),
    });
    const newRep = {
      id: res.id,
      status: res.status || 'queued',
      ...reportData,
      captured_at: reportData.captured_at || new Date().toISOString(),
    };
    sessionReports.unshift(newRep);
    return res;
  }

  await simulateLatency(250);
  const nextId = `REP-${String(sessionReports.length + 1).padStart(3, '0')}`;
  const newReport = {
    id: nextId,
    status: 'queued',
    zone_id: reportData.zone_id || 'S2',
    type: reportData.type || 'crack',
    text: reportData.text || '',
    lat: reportData.lat ?? 27.3381,
    lon: reportData.lon ?? 88.6121,
    captured_at: new Date().toISOString(),
    reporter: reportData.reporter || 'field-officer-fixture',
    photo: 'fixture-only (no binary in repo)',
  };
  sessionReports.unshift(newReport);
  return { id: nextId, status: 'queued' };
}
