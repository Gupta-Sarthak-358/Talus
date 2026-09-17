// Simple credential gate for SIH demo — same app, role-gated pages.
// Villager: open. Officer/state/rescue/admin: PIN. Stored in localStorage.
// No backend auth yet (post-hackathon: real JWT). Admin PIN 9999 can open all.

const STORE_KEY = 'talus_auth';

const PINS = {
  villager: '',          // open
  district_officer: '1111',
  state_manager: '2222',
  rescue_team: '3333',
  admin: '9999',
};

export function getAuth() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    return raw ? JSON.parse(raw) : { role: 'villager', at: null };
  } catch { return { role: 'villager', at: null }; }
}

export function setAuth(role) {
  const rec = { role, at: new Date().toISOString() };
  try { localStorage.setItem(STORE_KEY, JSON.stringify(rec)); } catch {}
  return rec;
}

export function clearAuth() {
  try { localStorage.removeItem(STORE_KEY); } catch {}
}

export function canAccess(requestedRole, authRole) {
  if (requestedRole === 'villager') return true;
  if (authRole === 'admin') return true;
  return authRole === requestedRole;
}

export function checkPin(role, pin) {
  const expected = PINS[role];
  if (expected === undefined) return false;
  if (expected === '') return true;
  return String(pin) === expected;
}

export function roleLabel(role) {
  const m = { villager:'Villager', district_officer:'District Officer', state_manager:'State Manager', rescue_team:'Rescue Team', admin:'Admin' };
  return m[role] || role;
}

export const DEMO_PINS = PINS;
