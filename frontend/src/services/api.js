/**
 * Base API Client for Talus — LIVE ONLY (SIH26001)
 * No mock fallback. All data via FastAPI. Offline resilience is via fixture-backed live endpoints, not mock arrays.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Generic API request wrapper — live only
 */
export async function apiRequest(endpoint, options = {}) {

  const url = `${BASE_URL}${endpoint}`;
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API Error [${response.status}]: ${errorBody || response.statusText}`);
  }

  return response.json();
}

export const isLiveApiEnabled = () => true;
