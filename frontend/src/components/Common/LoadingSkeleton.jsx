import React from 'react';

export function LoadingSkeleton({ lines = 3, className = '' }) {
  return (
    <div className={`animate-pulse space-y-3 ${className}`}>
      <div className="h-4 bg-mine-border/60 rounded w-3/4"></div>
      {Array.from({ length: lines - 1 }).map((_, i) => (
        <div
          key={i}
          className="h-3 bg-mine-border/40 rounded"
          style={{ width: `${90 - i * 15}%` }}
        ></div>
      ))}
    </div>
  );
}

export function ErrorState({ title = 'Intelligence Service Unavailable', message, onRetry }) {
  return (
    <div className="p-6 bg-red-950/20 border border-red-800/40 rounded-xl text-center space-y-3">
      <div className="w-10 h-10 mx-auto rounded-full bg-red-500/10 flex items-center justify-center text-red-400">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h3 className="text-sm font-semibold text-red-200">{title}</h3>
      <p className="text-xs text-slate-400 max-w-sm mx-auto">
        {message || 'Unable to retrieve risk intelligence telemetry. Telemetry bridge offline.'}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-3 py-1.5 bg-red-900/40 hover:bg-red-800/60 border border-red-700 text-xs font-medium text-red-200 rounded transition-colors"
        >
          Retry Connection
        </button>
      )}
    </div>
  );
}
