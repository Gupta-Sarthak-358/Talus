/**
 * @deprecated — Use `../data/constants.js` instead. Kept only as re-export shim.
 * No mock arrays. Live data via /api/* only. MOCK_MULTILINGUAL_ALERT removed — use POST /api/alerts/dispatch live.
 */
export { RISK_BANDS, ROLES, WHAT_IF_PRESETS } from './constants';

// Removed: MOCK_MULTILINGUAL_ALERT — was fixture, now live only via POST /api/alerts/dispatch
// Keeping a null export so old imports fail fast instead of silently using stale fixture
export const MOCK_MULTILINGUAL_ALERT = null;
