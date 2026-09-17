import { apiRequest } from './api';

export async function getForecastLive(location = 'gangtok') {
  return apiRequest(`/forecast/live?location=${encodeURIComponent(location)}`);
}
export async function getForecastFixture() {
  return apiRequest('/forecast/rainfall');
}
