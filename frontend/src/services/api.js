/**
 * Base API Client for Talus
 * Allows toggling between offline mock mode (default for SIH demo reliability)
 * and live FastAPI endpoints when the backend is deployed.
 */

const USE_LIVE_API = import.meta.env.VITE_USE_LIVE_API === 'true';
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Helper to simulate network latency for authentic UI loading states in demo mode
 */
export async function simulateLatency(ms = 300) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Generic API request wrapper
 */
export async function apiRequest(endpoint, options = {}) {
  if (!USE_LIVE_API) {
    // When in mock mode, will be handled by individual mock service methods
    throw new Error('Live API is disabled; using mock service layer.');
  }

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

export const isLiveApiEnabled = () => USE_LIVE_API;
