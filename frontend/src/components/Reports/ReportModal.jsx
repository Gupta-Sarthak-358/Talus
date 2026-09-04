import React, { useState, useEffect } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import {
  savePhotoBackground, getAllPhotosBackground,
  saveReportOutbox, readReportOutbox,
  makePhotoThumbnail, sha256File,
} from '../../services/reports';
import { FileText, Send, X, Clock, MapPin, CheckCircle2, AlertCircle, RefreshCw, ShieldCheck, ImagePlus, Trash2, CloudOff } from 'lucide-react';

const ACCEPTED_MEDIA = ['image/jpeg', 'image/png', 'image/webp', 'video/mp4'];
const ACCEPT_ATTR = 'image/jpeg,image/png,image/webp,video/mp4';
const MAX_MEDIA_BYTES = 10 * 1024 * 1024; // 10 MB mockup cap (background store is localStorage)

/** Network-ish failures may queue to the background outbox; 4xx validation must not. */
function isOutboxEligible(err) {
  const msg = String(err?.message || err || '');
  if (/^API Error \[4(?!29)\d\d\]/.test(msg)) return false;
  return /Failed to fetch|NetworkError|Load failed|API Error \[(429|5\d\d)\]|Network request failed/i.test(msg);
}

export default function ReportModal() {
  const {
    isReportModalOpen,
    setIsReportModalOpen,
    reports,
    submitNewReport,
    refreshReports,
    zones,
    selectedZoneId,
    t,
  } = useTalusContext();

  const REPORT_TYPES = [
    { id: 'crack', label: t('reports.type_crack') },
    { id: 'slope_movement', label: t('reports.type_movement') },
    { id: 'blocked_road', label: t('reports.type_blocked') },
    { id: 'other', label: t('reports.type_other') },
  ];

  const REPORTER_ROLES = [
    { id: 'field_officer', label: t('reports.role_field') },
    { id: 'villager', label: t('role.villager') },
  ];

  const [formZone, setFormZone] = useState(selectedZoneId || 'S2');
  const [reportType, setReportType] = useState('crack');
  const [description, setDescription] = useState('');
  const [reporterRole, setReporterRole] = useState('field_officer');
  const [consent, setConsent] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(null);
  const [submitError, setSubmitError] = useState(null);
  const [submitInfo, setSubmitInfo] = useState(null);
  // Photo mockup lane: real local file, preview + sha256; bytes stay client-side
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [photoThumb, setPhotoThumb] = useState(null);
  const [photoHash, setPhotoHash] = useState(null);
  const [photoError, setPhotoError] = useState(null);
  const [hashing, setHashing] = useState(false);
  // Background store: thumbnails keyed by report id + pending outbox count
  const [photoMap, setPhotoMap] = useState({});
  const [outboxCount, setOutboxCount] = useState(0);

  useEffect(() => {
    if (isReportModalOpen) {
      setPhotoMap(getAllPhotosBackground());
      setOutboxCount(readReportOutbox().length);
    }
  }, [isReportModalOpen, reports]);

  if (!isReportModalOpen) return null;

  const activeZoneObj = zones.find((z) => z.id === formZone);
  const defaultLat = activeZoneObj?.geometry?.centroid?.[0] ?? 27.3381;
  const defaultLon = activeZoneObj?.geometry?.centroid?.[1] ?? 88.6121;

  const handlePhotoSelect = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    setPhotoError(null);
    if (!file) return;
    if (!ACCEPTED_MEDIA.includes(file.type)) {
      setPhotoError(`Unsupported type ${file.type || 'unknown'} — use JPEG/PNG/WebP/MP4 (flagged otherwise)`);
      return;
    }
    if (file.size > MAX_MEDIA_BYTES) {
      setPhotoError(`File too large (${(file.size / 1048576).toFixed(1)} MB > 10 MB mockup cap)`);
      return;
    }
    if (photoPreview) URL.revokeObjectURL(photoPreview);
    setPhotoFile(file);
    setPhotoPreview(file.type.startsWith('image/') ? URL.createObjectURL(file) : null);
    setHashing(true);
    try {
      const [hash, thumb] = await Promise.all([sha256File(file), makePhotoThumbnail(file)]);
      setPhotoHash(hash);
      setPhotoThumb(thumb);
    } finally {
      setHashing(false);
    }
  };

  const clearPhoto = () => {
    if (photoPreview) URL.revokeObjectURL(photoPreview);
    setPhotoFile(null);
    setPhotoPreview(null);
    setPhotoThumb(null);
    setPhotoHash(null);
    setPhotoError(null);
  };

  const handleSync = async () => {
    try {
      const pending = await refreshReports();
      setOutboxCount(pending);
      setPhotoMap(getAllPhotosBackground());
    } catch (err) {
      setSubmitError(err.message || t('reports.failed'));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!description.trim() || description.trim().length < 10) return;
    if (!consent) return;

    setSubmitting(true);
    setSubmitSuccess(null);
    setSubmitError(null);
    setSubmitInfo(null);
    try {
      const payload = {
        zone_id: formZone,
        type: reportType,
        text: description.trim(),
        lat: defaultLat,
        lon: defaultLon,
        captured_at: new Date().toISOString(),
        reporter_role: reporterRole,
        photo: photoFile ? {
          filename: photoFile.name,
          mime: photoFile.type,
          size_bytes: photoFile.size,
          sha256: photoHash || 'pending',
          exif_lat: defaultLat,
          exif_lon: defaultLon,
        } : null,
        consent: true,
      };
      const res = await submitNewReport(payload);
      if (photoThumb && res?.id) {
        savePhotoBackground(res.id, { dataUrl: photoThumb, filename: photoFile.name, mime: photoFile.type });
        setPhotoMap(getAllPhotosBackground());
      }
      setSubmitSuccess(res.id || 'Queued');
      setDescription('');
      clearPhoto();
    } catch (err) {
      if (photoFile && isOutboxEligible(err)) {
        // Background store: keep payload + thumbnail locally, flush on next Sync
        const payload = {
          zone_id: formZone,
          type: reportType,
          text: description.trim(),
          lat: defaultLat,
          lon: defaultLon,
          captured_at: new Date().toISOString(),
          reporter_role: reporterRole,
          photo: {
            filename: photoFile.name,
            mime: photoFile.type,
            size_bytes: photoFile.size,
            sha256: photoHash || 'pending',
            exif_lat: defaultLat,
            exif_lon: defaultLon,
          },
          consent: true,
        };
        saveReportOutbox({ payload, thumb: photoThumb });
        setOutboxCount(readReportOutbox().length);
        setSubmitInfo('Backend unreachable — report stored in background outbox, will sync on next Sync.');
        setDescription('');
        clearPhoto();
      } else {
        setSubmitError(err.message || t('reports.failed'));
      }
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
              <h3 className="text-sm font-bold text-mine-text">{t('reports.title')}</h3>
              <p className="text-[11px] text-mine-muted">
                {t('reports.observations_sub')}
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
                {t('reports.step1')}
              </h4>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                POST /api/reports
              </span>
            </div>

            {submitSuccess && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                <span>Report <strong>{submitSuccess}</strong> {t('reports.queued')}</span>
              </div>
            )}
            {submitError && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                <span>{submitError}</span>
              </div>
            )}
            {submitInfo && (
              <div className="p-3 bg-sky-500/10 border border-sky-500/30 rounded-lg text-xs text-sky-300 flex items-center gap-2">
                <CloudOff className="w-4 h-4 shrink-0 text-sky-400" />
                <span>{submitInfo}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3 bg-mine-darker p-3.5 rounded-xl border border-mine-border text-xs">
              <div>
                <label className="text-[11px] font-semibold text-mine-muted">{t('reports.slopeSector')}</label>
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
                <label className="text-[11px] font-semibold text-mine-muted">{t('reports.observationType')}</label>
                <div className="grid grid-cols-2 gap-1.5 mt-1">
                  {REPORT_TYPES.map((rt) => (
                    <button
                      type="button"
                      key={rt.id}
                      onClick={() => setReportType(rt.id)}
                      className={`px-2 py-1.5 rounded text-[11px] font-medium border text-left transition-all ${
                        reportType === rt.id
                          ? 'bg-talus-600 text-white border-talus-500 shadow-sm'
                          : 'bg-mine-card text-mine-muted border-mine-border hover:text-mine-text'
                      }`}
                    >
                      {rt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-mine-muted">{t('reports.reporterRole')}</label>
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
                <label className="text-[11px] font-semibold text-mine-muted">{t('reports.description')}</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder={t('reports.placeholder')}
                  className="w-full mt-1 bg-mine-card border border-mine-border rounded-lg p-2 text-xs text-mine-text focus:outline-none focus:border-talus-500 resize-none"
                  required
                  minLength={10}
                />
              </div>

              {/* Photo mockup lane: real local file, preview + sha256; bytes stay client-side */}
              <div>
                <label className="text-[11px] font-semibold text-mine-muted">Photo / Video <span className="font-normal">(mockup — stored in background, metadata posted)</span></label>
                <input
                  type="file"
                  accept={ACCEPT_ATTR}
                  onChange={handlePhotoSelect}
                  className="hidden"
                  id="report-photo-input"
                />
                {!photoFile ? (
                  <label
                    htmlFor="report-photo-input"
                    className="mt-1 flex items-center justify-center gap-2 w-full py-2.5 rounded-lg border border-dashed border-mine-border bg-mine-card text-mine-muted hover:text-mine-text hover:border-talus-500 cursor-pointer text-[11px] transition-colors"
                  >
                    <ImagePlus className="w-4 h-4" />
                    <span>Attach photo / video (JPEG/PNG/WebP/MP4, ≤10 MB)</span>
                  </label>
                ) : (
                  <div className="mt-1 p-2 rounded-lg border border-mine-border bg-mine-card flex items-center gap-2.5">
                    {photoPreview ? (
                      <img src={photoPreview} alt="attachment preview" className="w-14 h-14 rounded-md object-cover border border-mine-border shrink-0" />
                    ) : (
                      <div className="w-14 h-14 rounded-md bg-mine-darker border border-mine-border flex items-center justify-center shrink-0 text-[9px] font-mono text-mine-muted">VIDEO</div>
                    )}
                    <div className="min-w-0 flex-1">
                      <div className="text-[11px] font-semibold text-mine-text truncate">{photoFile.name}</div>
                      <div className="text-[10px] font-mono text-mine-muted truncate">
                        {photoFile.type || 'unknown'} · {(photoFile.size / 1024).toFixed(1)} KB{hashing ? ' · hashing…' : photoHash ? ` · sha256:${photoHash.slice(0, 12)}…` : ''}
                      </div>
                      <div className="text-[10px] text-mine-muted">EXIF mocked to claimed GPS (mockup lane)</div>
                    </div>
                    <button type="button" onClick={clearPhoto} className="p-1.5 rounded-lg hover:bg-mine-dark text-mine-muted hover:text-red-400 transition-colors" title="Remove attachment">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
                {photoError && (
                  <p className="text-[10px] text-red-400 mt-1">{photoError}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div>
                  <span className="text-mine-muted">{t('reports.gpsLat')}</span>
                  <div className="font-mono text-mine-text mt-0.5">{defaultLat.toFixed(4)}° N</div>
                </div>
                <div>
                  <span className="text-mine-muted">{t('reports.gpsLon')}</span>
                  <div className="font-mono text-mine-text mt-0.5">{defaultLon.toFixed(4)}° E</div>
                </div>
              </div>

              <label className="flex items-start gap-2 p-2 bg-mine-card border border-mine-border rounded-lg cursor-pointer">
                <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5" />
                <span className="text-[11px] text-mine-muted leading-tight">
                  {t('reports.consent')}
                </span>
              </label>

              <button
                type="submit"
                disabled={submitting || !description.trim() || description.trim().length < 10 || !consent}
                className="w-full flex items-center justify-center gap-2 py-2 bg-talus-600 hover:bg-talus-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold transition-all shadow-sm mt-2"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{submitting ? t('reports.queuing') : t('reports.submitBtn')}</span>
              </button>
              <p className="text-[10px] text-mine-muted text-center">{t('reports.exif_note')}</p>
            </form>
          </div>

          {/* Right: In-Memory / Server Report Queue */}
          <div className="md:col-span-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h4 className="text-xs font-bold text-mine-text uppercase tracking-wider">
                  {t('reports.step2')}
                </h4>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-talus-600/20 text-talus-600">
                  {reports.length}
                </span>
              </div>

              <button
                onClick={handleSync}
                className="text-[11px] text-mine-muted hover:text-talus-600 flex items-center gap-1 transition-colors"
                title={t('reports.refresh_title')}
              >
                <RefreshCw className="w-3 h-3" />
                <span>{t('reports.sync')}</span>
                {outboxCount > 0 && (
                  <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-sky-500/15 text-sky-400 border border-sky-500/30">
                    {outboxCount} pending
                  </span>
                )}
              </button>
            </div>

            {outboxCount > 0 && (
              <div className="p-2.5 bg-sky-500/10 border border-sky-500/30 rounded-xl text-[11px] text-sky-300 flex items-center gap-2">
                <CloudOff className="w-4 h-4 shrink-0 text-sky-400" />
                <span>{outboxCount} report{outboxCount === 1 ? '' : 's'} stored in background outbox — press Sync to flush when back online.</span>
              </div>
            )}

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

                  <div className="flex items-start gap-2.5">
                    {photoMap[rep.id]?.dataUrl && (
                      <img src={photoMap[rep.id].dataUrl} alt={`attachment for ${rep.id}`} className="w-16 h-16 rounded-lg object-cover border border-mine-border shrink-0" />
                    )}
                    <p className="text-mine-text text-[11px] leading-relaxed flex-1">
                      "{rep.text}"
                    </p>
                  </div>

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
          {t('reports.offlineNote')}
        </div>
      </div>
    </div>
  );
}
