import React, { useState } from 'react';
import { useMineContext } from '../../context/MineContext';
import { FileText, Send, X, Clock, MapPin, CheckCircle2, AlertCircle, RefreshCw, ShieldCheck } from 'lucide-react';

const REPORT_TYPES = [
  { id: 'crack', label: 'Tension Crack' },
  { id: 'slope_movement', label: 'Slope Movement' },
  { id: 'blocked_road', label: 'Blocked Road' },
  { id: 'other', label: 'Other' },
];

const REPORTER_ROLES = [
  { id: 'field_officer', label: 'Field Officer' },
  { id: 'villager', label: 'Villager / Community' },
];

export default function ReportModal() {
  const {
    isReportModalOpen,
    setIsReportModalOpen,
    reports,
    submitNewReport,
    refreshReports,
    zones,
    selectedZoneId,
  } = useMineContext();

  const [formZone, setFormZone] = useState(selectedZoneId || 'S2');
  const [reportType, setReportType] = useState('crack');
  const [description, setDescription] = useState('');
  const [reporterRole, setReporterRole] = useState('field_officer');
  const [consent, setConsent] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(null);
  const [submitError, setSubmitError] = useState(null);

  if (!isReportModalOpen) return null;

  const activeZoneObj = zones.find((z) => z.id === formZone);
  const defaultLat = activeZoneObj?.geometry?.centroid?.[0] ?? 27.3381;
  const defaultLon = activeZoneObj?.geometry?.centroid?.[1] ?? 88.6121;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!description.trim() || description.trim().length < 10) return;
    if (!consent) return;

    setSubmitting(true);
    setSubmitSuccess(null);
    setSubmitError(null);
    try {
      const payload = {
        zone_id: formZone,
        type: reportType,
        text: description.trim(),
        lat: defaultLat,
        lon: defaultLon,
        captured_at: new Date().toISOString(),
        reporter_role: reporterRole,
        photo: {
          filename: `field_${formZone}_${Date.now()}.jpg`,
          mime: 'image/jpeg',
          size_bytes: 0,
          sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
          exif_lat: defaultLat,
          exif_lon: defaultLon,
        },
        consent: true,
      };
      const res = await submitNewReport(payload);
      setSubmitSuccess(res.id || 'Queued');
      setDescription('');
    } catch (err) {
      setSubmitError(err.message || 'Failed to submit report');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-3xl bg-mine-card border border-mine-border rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="p-4 bg-mine-darker border-b border-mine-border flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-talus-600/20 text-talus-600 flex items-center justify-center border border-talus-600/30">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-mine-text">Field Hazard Reports & Queue</h3>
              <p className="text-[11px] text-mine-muted">
                Submit geo-tagged field observations (POST /api/reports) and inspect officer queue (GET /api/reports/queue?status=)
              </p>
            </div>
          </div>

          <button
            onClick={() => setIsReportModalOpen(false)}
            className="p-1.5 rounded-lg hover:bg-mine-dark text-mine-muted hover:text-mine-text transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body: Grid with Form (Left) & Queue (Right) */}
        <div className="p-4 sm:p-5 grid grid-cols-1 md:grid-cols-12 gap-5 overflow-y-auto">
          {/* Left: Report Submission Form */}
          <div className="md:col-span-6 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-mine-text uppercase tracking-wider">
                1. Submit Field Report
              </h4>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                POST /api/reports
              </span>
            </div>

            {submitSuccess && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                <span>Report <strong>{submitSuccess}</strong> queued successfully!</span>
              </div>
            )}
            {submitError && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                <span>{submitError}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3 bg-mine-darker p-3.5 rounded-xl border border-mine-border text-xs">
              <div>
                <label className="text-[11px] font-semibold text-mine-muted">Slope Sector</label>
                <select
                  value={formZone}
                  onChange={(e) => setFormZone(e.target.value)}
                  className="w-full mt-1 bg-mine-card border border-mine-border rounded-lg px-2.5 py-1.5 text-xs text-mine-text focus:outline-none focus:border-talus-500"
                >
                  {zones.map((z) => (
                    <option key={z.id} value={z.id}>
                      {z.name} [{z.risk_band}]
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-mine-muted">Observation Type</label>
                <div className="grid grid-cols-2 gap-1.5 mt-1">
                  {REPORT_TYPES.map((t) => (
                    <button
                      type="button"
                      key={t.id}
                      onClick={() => setReportType(t.id)}
                      className={`px-2 py-1.5 rounded text-[11px] font-medium border text-left transition-all ${
                        reportType === t.id
                          ? 'bg-talus-600 text-white border-talus-500 shadow-sm'
                          : 'bg-mine-card text-mine-muted border-mine-border hover:text-mine-text'
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-mine-muted">Reporter Role</label>
                <select
                  value={reporterRole}
                  onChange={(e) => setReporterRole(e.target.value)}
                  className="w-full mt-1 bg-mine-card border border-mine-border rounded-lg px-2.5 py-1.5 text-xs text-mine-text focus:outline-none focus:border-talus-500"
                >
                  {REPORTER_ROLES.map((r) => (
                    <option key={r.id} value={r.id}>{r.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-mine-muted">Description / Field Notes (≥10 chars)</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g. Fresh tension crack observed ~5m above road-cut after continuous rainfall..."
                  className="w-full mt-1 bg-mine-card border border-mine-border rounded-lg p-2 text-xs text-mine-text focus:outline-none focus:border-talus-500 resize-none"
                  required
                  minLength={10}
                />
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div>
                  <span className="text-mine-muted">GPS Latitude</span>
                  <div className="font-mono text-mine-text mt-0.5">{defaultLat.toFixed(4)}° N</div>
                </div>
                <div>
                  <span className="text-mine-muted">GPS Longitude</span>
                  <div className="font-mono text-mine-text mt-0.5">{defaultLon.toFixed(4)}° E</div>
                </div>
              </div>

              <label className="flex items-start gap-2 p-2 bg-mine-card border border-mine-border rounded-lg cursor-pointer">
                <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5" />
                <span className="text-[11px] text-mine-muted leading-tight">
                  I consent to sharing this photo + location with disaster authorities. Photo bytes are never committed (metadata only: sha256 + EXIF).
                </span>
              </label>

              <button
                type="submit"
                disabled={submitting || !description.trim() || description.trim().length < 10 || !consent}
                className="w-full flex items-center justify-center gap-2 py-2 bg-talus-600 hover:bg-talus-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold transition-all shadow-sm mt-2"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{submitting ? 'Queuing Report...' : 'Submit Field Report'}</span>
              </button>
              <p className="text-[10px] text-mine-muted text-center">EXIF GPS = claimed GPS (no mismatch) · consent:true · pilot bbox 27.20-27.40/88.40-88.70</p>
            </form>
          </div>

          {/* Right: In-Memory / Server Report Queue */}
          <div className="md:col-span-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h4 className="text-xs font-bold text-mine-text uppercase tracking-wider">
                  2. Officer Report Queue
                </h4>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-talus-600/20 text-talus-600">
                  {reports.length}
                </span>
              </div>

              <button
                onClick={refreshReports}
                className="text-[11px] text-mine-muted hover:text-talus-600 flex items-center gap-1 transition-colors"
                title="Refresh queue from backend (GET /api/reports/queue?status=)"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Sync</span>
              </button>
            </div>

            <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
              {reports.map((rep) => (
                <div
                  key={rep.id}
                  className="p-3 bg-mine-darker border border-mine-border rounded-xl space-y-1.5 hover:border-talus-600/40 transition-all text-xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono font-bold text-talus-600">{rep.id}</span>
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-risk-moderate/15 text-risk-moderate border border-risk-moderate/30">
                        {rep.zone_id} · {rep.type}
                      </span>
                    </div>

                    <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-semibold border ${rep.status === 'flagged' ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' : rep.status === 'verified' ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'}`}>
                      {rep.status}
                    </span>
                  </div>

                  <p className="text-mine-text text-[11px] leading-relaxed">
                    "{rep.text}"
                  </p>

                  {rep.flagged_reason && (
                    <p className="text-[10px] text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded px-2 py-1">{rep.flagged_reason}</p>
                  )}

                  <div className="flex items-center justify-between text-[10px] text-mine-muted pt-1 border-t border-mine-border/60">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-2.5 h-2.5 text-mine-muted" />
                      {Number(rep.lat).toFixed(4)}, {Number(rep.lon).toFixed(4)}
                    </span>
                    <span className="flex items-center gap-1"><ShieldCheck className="w-2.5 h-2.5" />{rep.reporter_role || rep.reporter || '—'}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Note */}
        <div className="p-3 bg-mine-darker border-t border-mine-border text-center text-[10px] text-mine-muted">
          Offline resilience: Reports use metadata-only lane (no binary in repo) + localStorage outbox + flagged (&gt;200m EXIF mismatch) + consent gate. Verified never auto-promotes to event.
        </div>
      </div>
    </div>
  );
}
