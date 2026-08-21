import React from 'react';
import { AlertTriangle, Database, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function MissingEvidenceCard({
  missingEvidence = [],
  confidence = 76,
  warningText = 'Risk should be interpreted with incomplete evidence.',
}) {
  const hasMissingEvidence = missingEvidence && missingEvidence.length > 0;

  if (!hasMissingEvidence) {
    return (
      <div className="bg-mine-darker/90 border border-mine-border rounded-xl p-3.5 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-slate-300">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>Telemetry Evidence: <strong>Complete</strong> (All sensors operational)</span>
        </div>
        <span className="font-mono text-emerald-400 font-bold">{confidence}% Confidence</span>
      </div>
    );
  }

  return (
    <div className="bg-amber-950/20 border border-amber-500/40 rounded-xl p-4 shadow-md space-y-2.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-amber-300">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <h4 className="text-xs font-bold uppercase tracking-wider">
            Evidence Quality & Uncertainty Warning
          </h4>
        </div>
        <span className="text-[11px] font-mono font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30">
          {confidence}% Confidence
        </span>
      </div>

      <p className="text-xs text-amber-200/90 font-medium">
        {warningText}
      </p>

      <div className="space-y-1.5 pt-1">
        <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
          Missing / Degraded Signals:
        </div>
        {missingEvidence.map((item, i) => (
          <div
            key={i}
            className="flex items-start gap-2 text-[11px] bg-mine-card/80 p-2 rounded-lg border border-mine-border/80"
          >
            <span className="text-amber-400 font-bold shrink-0">⚠</span>
            <div className="space-y-0.5">
              <div className="font-semibold text-slate-200">
                {typeof item === 'string' ? item : item.sensor}
              </div>
              {item.reason && (
                <div className="text-[10px] text-slate-400">
                  {item.reason} — <span className="text-slate-300">{item.impact}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="text-[10px] text-slate-400 border-t border-amber-500/20 pt-1.5">
        Talus ML Engine dynamically discounts risk confidence when critical geotechnical telemetry streams degrade.
      </div>
    </div>
  );
}
