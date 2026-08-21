import React from 'react';
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
        <div className="bg-mine-card border border-mine-border p-2 rounded-lg shadow-xl text-xs font-mono">
          <div className="text-slate-400 font-sans">{data.label || label}</div>
          <div className="font-bold text-orange-400 mt-0.5">
            Risk Score: {data.risk} / 100
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-mine-darker/90 border border-mine-border rounded-xl p-4 shadow-md space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <TrendingUp className="w-4 h-4 text-orange-400" />
          <h4 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
            Risk Escalation Timeline
          </h4>
        </div>
        <span className="text-[11px] font-mono text-red-400 font-semibold bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
          {trend.delta || '↑ Rising Rapidly'}
        </span>
      </div>

      <p className="text-[11px] text-slate-400">
        {trend.historySource === 'frozen_corpus_daily'
          ? 'Deterministic daily instability series (365 days, frozen corpus world seed 91):'
          : 'Temporal tracking over the active shift (09:00 – Present):'}
      </p>

      {/* Chart Canvas */}
      <div className="h-44 w-full pt-1">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={history} margin={{ top: 8, right: 12, left: -24, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#233354" vertical={false} />
            <XAxis
              dataKey="time"
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#233354' }}
              minTickGap={48}
            />
            <YAxis
              domain={[0, 100]}
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#233354' }}
              ticks={[0, 40, 65, 85, 100]}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Frozen risk-band thresholds (FoS-derived) */}
            <ReferenceLine y={75} stroke="#f97316" strokeDasharray="3 3" opacity={0.6}
              label={{ value: 'High', position: 'insideTopRight', fontSize: 9, fill: '#f97316' }} />
            <ReferenceLine y={85} stroke="#ef4444" strokeDasharray="3 3" opacity={0.6}
              label={{ value: 'Critical', position: 'insideTopRight', fontSize: 9, fill: '#ef4444' }} />

            <Line
              type="monotone"
              dataKey="risk"
              stroke="#f97316"
              strokeWidth={2}
              dot={history.length > 60 ? false : { r: 4, fill: '#f97316', stroke: '#0d131f', strokeWidth: 2 }}
              activeDot={{ r: 5, fill: '#ef4444', stroke: '#fff', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between text-[10px] text-slate-400 border-t border-mine-border/60 pt-2 font-mono">
        <span className="flex items-center gap-1">
          <span className="w-2 h-0.5 bg-orange-400 inline-block"></span> High Threshold (75)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-0.5 bg-red-500 inline-block"></span> Critical Threshold (85)
        </span>
      </div>
    </div>
  );
}
