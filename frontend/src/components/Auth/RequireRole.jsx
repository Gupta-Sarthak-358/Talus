import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { useTalusContext } from '../../context/TalusContext';
import { getAuth, canAccess } from '../../services/auth';
import LoginModal from './LoginModal';

/**
 * Route guard for officer shells + admin (SIH26001).
 * Villager stays open; district/state/rescue/admin need PIN — including direct URL entry.
 * Decision uses the stored grant (localStorage), never the context default, so a fresh
 * load can't slip through. Subscribes to context so PIN login flips the gate in one
 * click with no second navigation (already on target → just render children).
 */
export default function RequireRole({ allow, children }) {
  const { role: ctxRole, setRole } = useTalusContext();
  const location = useLocation();
  const needs = Array.isArray(allow) ? allow : [allow];
  // Re-read every render; ctxRole subscription re-renders this gate right after PIN login.
  void ctxRole;
  const stored = getAuth().role || 'villager';
  const ok = needs.some((r) => canAccess(r, stored));
  const [showLogin, setShowLogin] = useState(false);

  // Direct URL entry with no grant → PIN modal immediately, no extra click.
  useEffect(() => { if (!ok) setShowLogin(true); }, [ok, location.pathname]);

  if (ok) return <>{children}</>;
  const primary = needs[0];
  return (
    <main className="max-w-md mx-auto px-4 py-16 text-center space-y-4">
      <Shield className="w-10 h-10 text-zinc-400 mx-auto" />
      <h2 className="text-lg font-extrabold text-mine-text">Credentials required</h2>
      <p className="text-sm text-mine-muted">
        This {primary === 'admin' ? 'panel' : 'page'} needs an officer PIN. Villagers use the open page.
      </p>
      <button
        onClick={() => setShowLogin(true)}
        className="px-4 py-2 bg-zinc-900 text-white rounded-xl text-sm font-bold focus-visible:ring-2"
      >
        Unlock with PIN
      </button>
      {showLogin && (
        <LoginModal
          wantedRole={primary}
          allowAdminPin
          onClose={() => setShowLogin(false)}
          onSuccess={(r) => { setShowLogin(false); setRole(r); }}
        />
      )}
    </main>
  );
}
