import React from 'react';
import { useTalusContext } from '../../context/TalusContext';
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
import { TrendingUp, Clock, AlertCircle } from 'lucide-react';

export default function RiskTrendChart({ trend = {}, zoneName = 'Zone B' }) {
  const { t } = useTalusContext();
  const history = trend.history || [
    { time: '09:00', risk: 41, label: '09:00 AM' },
    { time: '10:00', risk: 53, label: '10:00 AM' },
    { time: '11:00', risk: 68, label: '11:00 AM' },
    { time: '12:00', risk: 78, label: '12:00 PM' },
    { time: '13:00', risk: 82, label: '01:00 PM (Live)' },
  ];

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-mine-card border border-mine-border p-2 rounded-lg shadow-md text-xs font-mono">
          <div className="text-mine-muted font-sans">{data.label || label}</div>
          <div className="font-bold text-risk-high mt-0.5">
            Risk Score: {data.risk} / 100
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-mine-darker border border-mine-border rounded-xl p-4 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <TrendingUp className="w-4 h-4 text-risk-high" />
          <h4 className="text-xs font-bold text-mine-text uppercase tracking-wider">
            {t('zone.trend')}
          </h4>
        </div>
        <span className="text-[11px] font-mono text-risk-critical font-semibold bg-risk-critical/15 px-2 py-0.5 rounded border border-risk-critical/30">
          {trend.delta || t('trend.rising')}
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
    </div>
  );
}
