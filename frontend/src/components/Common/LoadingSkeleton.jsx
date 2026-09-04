import React from 'react';
import { useTalusContext } from '../../context/TalusContext';

export function LoadingSkeleton({ lines = 3, className = '' }) {
  return (
    <div className={`animate-pulse space-y-3 ${className}`}>
      <div className="h-4 bg-mine-border rounded w-3/4"></div>
      {Array.from({ length: lines - 1 }).map((_, i) => (
        <div
          key={i}
          className="h-3 bg-mine-border/60 rounded"
          style={{ width: `${90 - i * 15}%` }}
        ></div>
      ))}
    </div>
  );
}

export function ErrorState({ title = null, message, onRetry }) {
  const { t } = useTalusContext();
  const heading = title || t('common.unavailable');
  const body = message || t('common.telemetry_offline');
  return (
    <div className="p-6 bg-mine-darker border border-risk-critical/30 rounded-xl text-center space-y-3">
      <div className="w-10 h-10 mx-auto rounded-full bg-risk-critical/15 flex items-center justify-center text-risk-critical">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h3 className="text-sm font-semibold text-mine-text">{heading}</h3>
      <p className="text-xs text-mine-muted max-w-sm mx-auto">
        {body}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-3 py-1.5 bg-mine-card hover:bg-mine-dark border border-mine-border text-xs font-medium text-mine-text rounded transition-colors"
        >
          {t('common.retry_conn')}
        </button>
      )}
    </div>
  );
}
