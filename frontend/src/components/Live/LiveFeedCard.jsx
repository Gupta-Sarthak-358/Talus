import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Radio, QrCode, AlertTriangle, BatteryLow, WifiOff } from 'lucide-react';
import { apiRequest } from '../../services/api';

const POLL_MS = 5000;
const ZONE_ORDER = ['S1', 'S2', 'S3', 'S4', 'N1', 'N2', 'N3', 'N4', 'D1', 'D2', 'D3', 'D4'];

/**
 * Live simulator card (Lab lane). Polls GET /api/live/feed (+ audit tail)
 * while scripts/local_sensor_sim.py ticks; falls back to the committed
 * SIMULATED sample when the simulator is off, and to an honest offline
 * badge when the backend is unreachable. Never implies real sensors:
 * every state carries a SIMULATED label.
 */
export default function LiveFeedCard() {
  const [feed, setFeed] = useState(null);
  const [servedFrom, setServedFrom] = useState(null);
  const [audit, setAudit] = useState([]);
  const [offline, setOffline] = useState(false);
  const [qrZone, setQrZone] = useState('S1');
  const timer = useRef(null);

  const poll = useCallback(async () => {
    try {
      const f = await apiRequest('/live/feed');
      setFeed(f.feed);
      setServedFrom(f.served_from);
      try {
        const a = await apiRequest('/live/audit?limit=3');
        setAudit(a.events || []);
      } catch {
        setAudit([]);
      }
      setOffline(false);
    } catch {
      setOffline(true);
    }
  }, []);

  useEffect(() => {
    poll();
    timer.current = setInterval(poll, POLL_MS);
    return () => clearInterval(timer.current);
  }, [poll]);

  const reportUrl = `${window.location.origin}/reports?zone=${qrZone}&tick=${feed?.tick ?? 0}&sim=1`;
  const qrImg = `https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=${encodeURIComponent(reportUrl)}`;

  return (
    <div className="bg-mine-card border border-mine-border rounded-2xl overflow-hidden">
      <div className="p-4 bg-mine-darker border-b border-mine-border flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-bold text-mine-text">{t('live.sensorTitle')}</h3>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">
            SIMULATED
          </span>
        </div>
        <div className="text-[11px] text-mine-muted">
          {offline ? (
            <span className="inline-flex items-center gap-1 text-red-300">
              <WifiOff className="w-3.5 h-3.5" /> backend unreachable — showing last tick
            </span>
          ) : feed ? (
            <span>
              tick <span className="font-mono font-bold text-mine-text">{feed.tick}</span>
              {' · '}seed {feed.seed}
              {' · '}via <span className="font-mono">{servedFrom === 'simulator' ? 'local simulator' : 'committed sample'}</span>
            </span>
          ) : (
            'connecting…'
          )}
        </div>
      </div>

      {feed ? (
        <div className="p-4 grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-7 overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="text-left text-mine-muted border-b border-mine-border">
                  <th className="py-1 pr-2">zone</th>
                  <th className="py-1 pr-2">rain 1h (mm)</th>
                  <th className="py-1 pr-2">Δ soil</th>
                  <th className="py-1 pr-2">batt</th>
                  <th className="py-1 pr-2">rssi</th>
                  <th className="py-1">status</th>
                </tr>
              </thead>
              <tbody>
                {ZONE_ORDER.map((zid) => {
                  const z = feed.zones[zid];
                  if (!z) return null;
                  return (
                    <tr key={zid} className="border-b border-mine-border/50 font-mono">
                      <td className="py-1 pr-2 font-bold">{zid}</td>
                      <td className="py-1 pr-2">{z.rain_1h_mm.toFixed(2)}</td>
                      <td className="py-1 pr-2">{z.soil_delta >= 0 ? '+' : ''}{z.soil_delta.toFixed(4)}</td>
                      <td className="py-1 pr-2">
                        <span className="inline-flex items-center gap-1">
                          {z.battery_pct < 20 && <BatteryLow className="w-3 h-3 text-amber-300" />}
                          {z.battery_pct.toFixed(0)}%
                        </span>
                      </td>
                      <td className="py-1 pr-2">{z.rssi_dbm.toFixed(0)} dBm</td>
                      <td className="py-1">
                        {z.status === 'ok' ? (
                          <span className="text-emerald-300">ok</span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-amber-300">
                            <AlertTriangle className="w-3 h-3" />{z.status}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="text-[10px] text-mine-muted mt-2">
              issued {feed.issued_at} · deterministic seed {feed.seed} ({feed.sim}) · sensor deltas only — risk scores unchanged
            </p>
          </div>

          <div className="lg:col-span-5 space-y-3">
            <div className="border border-mine-border rounded-xl p-3">
              <div className="flex items-center gap-2 mb-2">
                <QrCode className="w-4 h-4 text-sky-400" />
                <h4 className="text-xs font-bold text-mine-text">Judge-phone live report</h4>
              </div>
              <div className="flex items-center gap-2 mb-2">
                <label className="text-[11px] text-mine-muted" htmlFor="qr-zone">zone</label>
                <select
                  id="qr-zone"
                  value={qrZone}
                  onChange={(e) => setQrZone(e.target.value)}
                  className="bg-mine-darker border border-mine-border rounded-lg text-xs px-2 py-1"
                >
                  {ZONE_ORDER.map((z) => <option key={z} value={z}>{z}</option>)}
                </select>
              </div>
              <div className="flex gap-3 items-start">
                <img src={qrImg} alt={`QR for live report ${qrZone}`} width={140} height={140}
                  className="rounded-lg border border-mine-border bg-white" loading="lazy" />
                <div className="text-[11px] text-mine-muted break-all">
                  <p>{t('live.qrHint')} <span className="font-bold text-mine-text">{qrZone}</span> at tick <span className="font-mono">{feed.tick}</span>.</p>
                  <p className="mt-1 font-mono text-[10px]">{reportUrl}</p>
                  <p className="mt-1">QR needs internet (qrserver); the URL works offline on the demo LAN.</p>
                </div>
              </div>
            </div>

            <div className="border border-mine-border rounded-xl p-3">
              <h4 className="text-xs font-bold text-mine-text mb-2">{t('live.auditTitle')}</h4>
              {audit.length === 0 ? (
                <p className="text-[11px] text-mine-muted">{t('live.noAudit')}</p>
              ) : (
                <ul className="text-[11px] font-mono space-y-1">
                  {audit.map((ev, i) => (
                    <li key={i} className="text-mine-muted">
                      <span className="text-mine-text">t{ev.tick}</span> {ev.event} — {ev.detail}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="p-6 text-center text-xs text-mine-muted">
          {offline ? 'Backend offline. Start it (start_all.ps1), then start the simulator.' : 'Loading live feed…'}
        </div>
      )}
    </div>
  );
}
