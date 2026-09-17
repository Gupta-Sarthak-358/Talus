import React, { useState } from 'react';
import { Shield, X, Lock } from 'lucide-react';
import { checkPin, setAuth, roleLabel } from '../../services/auth';
import { useTalusContext } from '../../context/TalusContext';

export default function LoginModal({ wantedRole, onClose, onSuccess }) {
  const [pin, setPin] = useState('');
  const [err, setErr] = useState('');
  const { setRole } = useTalusContext();

  const handle = (e) => {
    e.preventDefault();
    if (checkPin(wantedRole, pin)) {
      setAuth(wantedRole);
      setRole(wantedRole);
      onSuccess?.(wantedRole);
      onClose?.();
    } else {
      setErr('Wrong PIN. Demo: district 1111 · state 2222 · rescue 3333 · admin 9999');
    }
  };

  if (wantedRole === 'villager') return null;
  return (
    <div className="fixed inset-0 z-[3000] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <form onSubmit={handle} className="w-full max-w-sm bg-mine-card border border-mine-border rounded-2xl shadow-xl overflow-hidden">
        <div className="px-4 py-3 bg-mine-darker border-b border-mine-border flex items-center justify-between">
          <span className="flex items-center gap-2 text-sm font-bold text-mine-text">
            <Shield className="w-4 h-4 text-talus-600" /> {roleLabel(wantedRole)} login
          </span>
          <button type="button" onClick={onClose} className="p-1 rounded hover:bg-mine-dark text-mine-muted"><X className="w-4 h-4" /></button>
        </div>
        <div className="p-4 space-y-3">
          <p className="text-xs text-mine-muted">This section needs credentials. Villagers use the open page; officers use PIN.</p>
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-mine-muted" />
            <input
              autoFocus
              type="password"
              inputMode="numeric"
              placeholder="Enter PIN"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              className="flex-1 px-3 py-2 bg-mine-darker border border-mine-border rounded-lg text-sm text-mine-text placeholder:text-mine-muted focus:outline-none focus:border-talus-500"
            />
          </div>
          {err && <p className="text-xs text-red-400">{err}</p>}
          <button type="submit" className="w-full py-2 bg-talus-600 hover:bg-talus-500 text-white rounded-lg text-sm font-bold">Unlock</button>
          <p className="text-[11px] text-mine-muted text-center">Demo PINs shown above — real deployment uses SSO/JWT.</p>
        </div>
      </form>
    </div>
  );
}
