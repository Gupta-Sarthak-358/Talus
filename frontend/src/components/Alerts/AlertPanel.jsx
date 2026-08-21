import React, { useState } from 'react';
import { useMineContext } from '../../context/MineContext';
import { Bell, ShieldAlert, AlertTriangle, CheckCircle2, X, ExternalLink, Filter } from 'lucide-react';

export default function AlertPanel() {
  const {
    alerts,
    handleAcknowledgeAlert,
    isAlertsDrawerOpen,
    setIsAlertsDrawerOpen,
    selectZone,
    role,
    currentRoleMeta,
  } = useMineContext();

  const [filterSeverity, setFilterSeverity] = useState('ALL');

  if (!isAlertsDrawerOpen) return null;

  const filteredAlerts = alerts.filter((a) => {
    if (filterSeverity === 'ALL') return true;
    return a.severity === filterSeverity;
  });

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-sm transition-opacity">
      <div className="w-full max-w-md bg-mine-card border-l border-mine-border h-full flex flex-col shadow-xl overflow-hidden animate-in slide-in-from-right duration-300">
        {/* Drawer Header */}
        <div className="p-4 bg-mine-darker border-b border-mine-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-risk-moderate/15 text-risk-moderate flex items-center justify-center">
              <Bell className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-mine-text">Active Risk Escalation Alerts</h3>
              <p className="text-[11px] text-mine-muted">Contextual mine hazard notifications</p>
            </div>
          </div>

          <button
            onClick={() => setIsAlertsDrawerOpen(false)}
            className="p-1.5 rounded-lg hover:bg-mine-dark text-mine-muted hover:text-mine-text transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Severity Filter Tabs */}
        <div className="px-4 py-2 bg-mine-darker border-b border-mine-border flex items-center justify-between text-xs">
          <div className="flex items-center gap-1">
            <Filter className="w-3 h-3 text-mine-muted" />
            <span className="text-mine-muted text-[11px]">Filter:</span>
          </div>
          <div className="flex gap-1">
            {['ALL', 'HIGH', 'MODERATE'].map((sev) => (
              <button
                key={sev}
                onClick={() => setFilterSeverity(sev)}
                className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${
                  filterSeverity === sev
                    ? 'bg-talus-600 text-white shadow-sm'
                    : 'text-mine-muted hover:text-mine-text'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>

        {/* Alerts List */}
        <div className="flex-1 p-4 space-y-3 overflow-y-auto">
          {filteredAlerts.length === 0 ? (
            <div className="p-8 text-center text-mine-muted text-xs">
              <CheckCircle2 className="w-8 h-8 text-risk-verylow mx-auto mb-2" />
              No active alerts matching the selected filter.
            </div>
          ) : (
            filteredAlerts.map((alert) => {
              const isHigh = alert.severity === 'HIGH' || alert.severity === 'CRITICAL';
              const roleDirective = alert.roleDirectives ? alert.roleDirectives[role] : null;

              return (
                <div
                  key={alert.id}
                  className={`p-3.5 rounded-xl border transition-all ${
                    alert.acknowledged
                      ? 'bg-mine-darker border-mine-border opacity-70'
                      : isHigh
                      ? 'bg-mine-darker border-risk-critical/40 shadow-sm'
                      : 'bg-mine-darker border-risk-moderate/30'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase font-mono ${
                          isHigh
                            ? 'bg-risk-critical/15 text-risk-critical border border-risk-critical/30'
                            : 'bg-risk-moderate/15 text-risk-moderate border border-risk-moderate/30'
                        }`}
                      >
                        {alert.severity}
                      </span>
                      <span className="text-[11px] text-mine-muted font-mono">{alert.timestamp}</span>
                    </div>

                    {!alert.acknowledged ? (
                      <button
                        onClick={() => handleAcknowledgeAlert(alert.id)}
                        className="text-[10px] font-semibold text-talus-600 hover:text-talus-700 flex items-center gap-1 transition-colors"
                      >
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Acknowledge</span>
                      </button>
                    ) : (
                      <span className="text-[10px] text-mine-muted italic">Acknowledged</span>
                    )}
                  </div>

                  <h4 className="text-xs font-bold text-mine-text mt-2 leading-snug">
                    {alert.title}
                  </h4>

                  <p className="text-[11px] text-mine-text mt-1 leading-relaxed">
                    {alert.summary}
                  </p>

                  {/* Primary Drivers Tags */}
                  {alert.drivers && alert.drivers.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {alert.drivers.map((d, i) => (
                        <span
                          key={i}
                          className="px-1.5 py-0.5 rounded bg-mine-card text-[10px] font-mono text-mine-muted border border-mine-border"
                        >
                          {d}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Role-Specific Directive */}
                  {roleDirective && (
                    <div className="mt-2.5 p-2 bg-mine-card border border-mine-border rounded-lg text-[11px]">
                      <div className="text-[10px] text-talus-600 font-bold uppercase">
                        Action for {currentRoleMeta.label}:
                      </div>
                      <div className="text-mine-text mt-0.5 font-medium">{roleDirective}</div>
                    </div>
                  )}

                  {/* Quick Action to Inspect Zone */}
                  <div className="mt-2.5 pt-2 border-t border-mine-border flex justify-end">
                    <button
                      onClick={() => {
                        selectZone(alert.zoneId);
                        setIsAlertsDrawerOpen(false);
                      }}
                      className="text-xs font-bold text-talus-600 hover:text-talus-700 flex items-center gap-1 transition-colors"
                    >
                      <span>Inspect {alert.zoneName.split('—')[0]} on Map</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
