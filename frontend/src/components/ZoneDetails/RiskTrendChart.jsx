import React, { useEffect, useState } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import { apiRequest } from '../../services/api';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import { TrendingUp, Minus } from 'lucide-react';

/**
 * Evidence-backed replay linkage (zone -> past-event case with a documented
 * geographic tie). S3: bundle states Lumsay ~1.1 km from S3 Tadong. S2: Upper
 * Sichey footprint; S2 previous_landslide=1 Upper Sichey @259m (sikkim_join).
 * Zones without a linked case render an honest empty state — never a fixture line.
 */
const REPLAY_LINK = {
  S3: 'lumsay-jun2022',
  S2: 'sichey-jun2021',
};

export default function RiskTrendChart({ zoneId = null, zoneName = '' }) {
  const { t } = useTalusContext();
  const [bundle, setBundle] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let stop = false;
    apiRequest('/replay/series')
      .then((b) => { if (!stop) setBundle(b); })
      .catch(() => { if (!stop) setFailed(true); });
    return () => { stop = true; };
  }, []);

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-mine-card border border-mine-border p-2 rounded-lg shadow-md text-xs font-mono">
          <div className="text-mine-muted font-sans">{data.time}</div>
          <div className="font-bold text-risk-high mt-0.5">
            Risk Score: {data.risk} / 100 [{data.band}]
          </div>
        </div>
      );
    }
    return null;
  };

  const header = (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-1.5">
        <TrendingUp className="w-4 h-4 text-risk-high" />
        <h4 className="text-xs font-bold text-mine-text uppercase tracking-wider">
          {t('zone.trend')}
        </h4>
      </div>
    </div>
  );

  if (failed || !bundle) {
    return (
      <div className="bg-mine-darker border border-mine-border rounded-xl p-4 shadow-sm space-y-3">
        {header}
        <p className="text-[11px] text-mine-muted">
          {failed
            ? 'Replay evidence unreachable — backend offline. No timeline invented.'
            : 'Loading replay evidence…'}
        </p>
      </div>
    );
  }

  const active = bundle.cases.find((c) => c.id === REPLAY_LINK[zoneId]) || null;
  if (!active) {
    return (
      <div className="bg-mine-darker border border-mine-border rounded-xl p-4 shadow-sm space-y-3">
        {header}
        <p className="text-[11px] text-mine-muted">
          No replay coverage for {zoneId || zoneName || 'this zone'} — replay covers 5 past
          Sikkim events (S2 Sichey, S3 Lumsay + Mangan, Dipudara, NH-10). Open Lab →
          Replay for the full date-gated series. No demo timeline shown.
        </p>
      </div>
    );
  }

  const history = active.series.map((r) => ({ time: r.date, risk: r.score, band: r.band }));
  const scores = active.series.map((r) => r.score);
  const last3 = scores.slice(-3);
  const deltas = [last3[1] - last3[0], last3[2] - last3[1]];
  const rapid = last3.length === 3 && (deltas.every((d) => d >= 8) || (deltas[0] + deltas[1]) >= 25);
  const rising = rapid || scores[scores.length - 1] > scores[0];

  return (
    <div className="bg-mine-darker border border-mine-border rounded-xl p-4 shadow-sm space-y-3">
      {header}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <span className="text-[11px] text-mine-muted">
          {active.site_name} · event {active.event_date}
        </span>
        <span className="text-[11px] font-mono font-semibold bg-risk-critical/15 px-2 py-0.5 rounded border border-risk-critical/30 flex items-center gap-1">
          {rising ? <TrendingUp className="w-3 h-3 text-risk-critical" /> : <Minus className="w-3 h-3 text-mine-muted" />}
          <span className={rising ? 'text-risk-critical' : 'text-mine-muted'}>{rising ? t('trend.rising') : t('trend.stable')}</span>
        </span>
      </div>

      <p className="text-[11px] text-mine-muted">
      </p>

      {/* Chart Canvas */}
      <div className="h-44 w-full pt-1">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={history} margin={{ top: 8, right: 12, left: -24, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d2c3b3" vertical={false} />
            <XAxis
              dataKey="time"
              stroke="#6f6256"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#d2c3b3' }}
              minTickGap={48}
            />
            <YAxis
              domain={[0, 100]}
              stroke="#6f6256"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#d2c3b3' }}
              ticks={[0, 40, 65, 85, 100]}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Frozen risk-band thresholds (FoS-derived) */}
            <ReferenceLine y={75} stroke="#d96b24" strokeDasharray="3 3" opacity={0.7}
              label={{ value: t('trend.high'), position: 'insideTopRight', fontSize: 9, fill: '#d96b24' }} />
            <ReferenceLine y={85} stroke="#c74732" strokeDasharray="3 3" opacity={0.7}
              label={{ value: t('trend.critical'), position: 'insideTopRight', fontSize: 9, fill: '#c74732' }} />
            <ReferenceLine x={active.event_date} stroke="#c74732" strokeDasharray="4 3" opacity={0.9}
              label={{ value: `EVENT ${active.event_date}`, position: 'insideTop', fontSize: 9, fill: '#c74732' }} />

            <Line
              type="monotone"
              dataKey="risk"
              stroke="#664930"
              strokeWidth={2}
              dot={history.length > 60 ? false : { r: 3, fill: '#664930', stroke: '#f3e9dd', strokeWidth: 1 }}
              activeDot={{ r: 5, fill: '#c74732', stroke: '#f3e9dd', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between text-[10px] text-mine-muted border-t border-mine-border pt-2 font-mono">
        <span className="flex items-center gap-1">
          <span className="w-2 h-0.5 bg-risk-high inline-block"></span> {t('trend.high_thr')}
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-0.5 bg-risk-critical inline-block"></span> {t('trend.crit_thr')}
        </span>
      </div>
      <div className="flex items-center justify-between text-[9px] font-mono px-1 pt-1 border-t border-dashed border-mine-border/60 mt-1">
        <span className="text-mine-muted">◀ REPLAY — score with inputs available ON each date only</span>
        <span className="px-1.5 py-0.5 rounded bg-mine-card border border-mine-border text-mine-text font-bold">EVENT ▼</span>
        <span className="text-mine-muted">no forecast beyond event day ▶</span>
      </div>
      <p className="text-[10px] text-mine-muted">Causality: replay_series uses only inputs available ON each date — no future leak. Case {active.id}; full ledger in Lab → Replay.</p>
    </div>
  );
}
