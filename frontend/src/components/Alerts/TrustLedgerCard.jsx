import React, { useEffect, useState } from 'react';
import { BadgeCheck } from 'lucide-react';
import { apiRequest } from '../../services/api';

/**
 * Trust ledger: warning reliability, not prediction accuracy. Aggregated from
 * the committed replay bundle (GET /api/replay/series): of 5 documented past
 * disasters, how many the system would have flagged High-or-worse before the
 * event day, with what lead time. Includes the former NH10 miss — fixed by
 * the event-anchored rain lane, kept visible as the reason the ledger exists.
 */
export default function TrustLedgerCard() {
  const [ledger, setLedger] = useState(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    let stop = false;
    apiRequest('/replay/series')
      .then((b) => { if (!stop) { setLedger(b.ledger); setOffline(false); } })
      .catch(() => { if (!stop) setOffline(true); });
    return () => { stop = true; };
  }, []);

  if (!ledger) {
    return offline ? (
      <div className="bg-mine-card border border-mine-border rounded-2xl p-4 text-xs text-mine-muted">
        Trust ledger unreachable — backend offline.
      </div>
    ) : null;
  }

  const detected = ledger.filter((L) => L.lead_high_days != null && L.lead_high_days >= 0);
  const leads = detected.map((L) => L.lead_high_days).sort((a, b) => a - b);
  const median = leads.length % 2
    ? leads[Math.floor(leads.length / 2)]
    : Math.round((leads[leads.length / 2 - 1] + leads[leads.length / 2]) / 2);
  const early = ledger.reduce((a, L) => a + (L.early_hot_episodes || 0), 0);

  return (
    <div className="bg-mine-card border border-mine-border rounded-2xl overflow-hidden">
      <div className="px-4 py-2.5 bg-mine-darker border-b border-mine-border flex items-center gap-2">
        <BadgeCheck className="w-4 h-4 text-emerald-300" />
        <span className="text-xs font-bold text-mine-text">Trust ledger — would the warnings have deserved action?</span>
      </div>
      <div className="px-4 py-3 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <div>
          <div className="text-xl font-bold font-mono text-mine-text">{detected.length}/{ledger.length}</div>
          <div className="text-[10px] text-mine-muted">past disasters flagged High+ before event day</div>
        </div>
        <div>
          <div className="text-xl font-bold font-mono text-mine-text">{median}d</div>
          <div className="text-[10px] text-mine-muted">median High-warning lead time</div>
        </div>
        <div>
          <div className="text-xl font-bold font-mono text-mine-text">{Math.min(...leads)}d</div>
          <div className="text-[10px] text-mine-muted">shortest lead (Sichey 2021)</div>
        </div>
        <div>
          <div className="text-xl font-bold font-mono text-mine-text">{early}</div>
          <div className="text-[10px] text-mine-muted">early hot episodes (reviewed, not hidden)</div>
        </div>
      </div>
      <div className="px-4 pb-3 overflow-x-auto">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="text-left text-mine-muted border-b border-mine-border">
              <th className="py-1 pr-2">event</th>
              <th className="py-1 pr-2">first High</th>
              <th className="py-1 pr-2">lead</th>
              <th className="py-1">first Critical</th>
            </tr>
          </thead>
          <tbody>
            {ledger.map((L) => (
              <tr key={L.id} className="border-b border-mine-border/50 text-mine-muted">
                <td className="py-1 pr-2 font-mono">{L.id}</td>
                <td className="py-1 pr-2 font-mono">{L.first_high || '—'}</td>
                <td className="py-1 pr-2 font-mono">{L.lead_high_days != null ? `${L.lead_high_days}d` : 'missed'}</td>
                <td className="py-1 font-mono">{L.first_critical || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-[10px] text-mine-muted mt-2">
          Computed from trailing-only inputs per replay day (causality asserted at bundle build).
          NH10 Oct-2022 was a miss under climatology rain and flags 25d early after the event-anchored fix.
        </p>
      </div>
    </div>
  );
}
