import React from 'react';
import { useTalusContext } from '../../context/TalusContext';
import { AlertTriangle, Database, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function MissingEvidenceCard({
  missingEvidence = [],
  confidence = 76,
  warningText = null,
}) {
  const { t } = useTalusContext();
  const hasMissingEvidence = missingEvidence && missingEvidence.length > 0;

  if (!hasMissingEvidence) {
    return (
      <div className="bg-mine-darker border border-mine-border rounded-xl p-3.5 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-mine-text">
          <CheckCircle2 className="w-4 h-4 text-risk-verylow" />
          <span>{t('miss.telemetry')} <strong>{t('miss.complete')}</strong> {t('miss.all_ops')}</span>
        </div>
        <span className="font-mono text-risk-verylow font-bold">{confidence}% Confidence</span>
      </div>
    );
  }

  return (
    <div className="bg-mine-darker border border-risk-moderate/40 rounded-xl p-4 shadow-sm space-y-2.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-risk-moderate">
          <AlertTriangle className="w-4 h-4 text-risk-moderate" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-mine-text">
            {t('miss.title')}
          </h4>
        </div>
        <span className="text-[11px] font-mono font-bold text-risk-moderate bg-risk-moderate/15 px-2 py-0.5 rounded border border-risk-moderate/30">
          {confidence}% Confidence
        </span>
      </div>

      <p className="text-xs text-mine-text font-medium">
        {warningText}
      </p>

      <div className="space-y-1.5 pt-1">
        <div className="text-[10px] uppercase font-bold text-mine-muted tracking-wider">
          {t('miss.missing')}
        </div>
        {missingEvidence.map((item, i) => (
          <div
            key={i}
            className="flex items-start gap-2 text-[11px] bg-mine-card p-2 rounded-lg border border-mine-border"
          >
            <span className="text-risk-moderate font-bold shrink-0">⚠</span>
            <div className="space-y-0.5">
              <div className="font-semibold text-mine-text">
                {typeof item === 'string' ? item : item.sensor}
              </div>
              {item.reason && (
                <div className="text-[10px] text-mine-muted">
                  {item.reason} — <span className="text-mine-text">{item.impact}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="text-[10px] text-mine-muted border-t border-mine-border pt-1.5">
        Talus ML Engine dynamically discounts risk confidence when critical geotechnical telemetry streams degrade.
      </div>
    </div>
  );
}
