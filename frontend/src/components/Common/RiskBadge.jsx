import React from 'react';
import { RISK_BANDS } from '../../data/constants';

export default function RiskBadge({ band = 'LOW', size = 'md', showDot = true, className = '' }) {
  const meta = RISK_BANDS[band] || RISK_BANDS.LOW;

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-1 font-semibold tracking-wider',
    lg: 'text-sm px-3.5 py-1.5 font-bold tracking-wider',
  };

  const dotSizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${meta.bg} ${meta.border} ${meta.color} ${sizeClasses[size] || sizeClasses.md} ${className}`}
    >
      {showDot && (
        <span
          className={`rounded-full ${dotSizes[size] || dotSizes.md} ${
            band === 'CRITICAL' ? 'animate-ping bg-risk-critical' : ''
          }`}
          style={{ backgroundColor: meta.badgeColor }}
        />
      )}
      <span>{meta.label}</span>
    </span>
  );
}
