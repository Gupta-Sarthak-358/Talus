import { apiRequest } from './api';

/**
 * Reports — LIVE SIH26001 (real /api/reports + /api/reports/queue?status=).
 * No mock fallback on 422 (validation) — only on network failure the caller may locally queue.
 *
 * Photo mockup lane (contract A§4: bytes never committed, metadata-only):
 * attached images stay client-side. A canvas-resized thumbnail dataURL is kept
 * in the background store (localStorage) keyed by report id for queue display;
 * the POST carries metadata only (filename/mime/size/sha256 + EXIF). Failed
 * submits land in the outbox and flush on the next Sync.
 */

const PHOTO_STORE_KEY = 'talus_report_photos';
const OUTBOX_KEY = 'talus_report_outbox';

function readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeJson(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false; // quota or privacy mode — photo simply won't persist
  }
}

export function savePhotoBackground(reportId, entry) {
  const all = readJson(PHOTO_STORE_KEY, {});
  all[reportId] = { ...entry, at: new Date().toISOString() };
  writeJson(PHOTO_STORE_KEY, all);
}

export function getPhotoBackground(reportId) {
  return readJson(PHOTO_STORE_KEY, {})[reportId] || null;
}

export function getAllPhotosBackground() {
  return readJson(PHOTO_STORE_KEY, {});
}

export function saveReportOutbox(entry) {
  const box = readJson(OUTBOX_KEY, []);
  box.push({ ...entry, outboxId: `PEND-${Date.now()}`, queuedAt: new Date().toISOString() });
  writeJson(OUTBOX_KEY, box);
}

export function readReportOutbox() {
  return readJson(OUTBOX_KEY, []);
}

export function dropReportOutbox(outboxId) {
  writeJson(OUTBOX_KEY, readJson(OUTBOX_KEY, []).filter((e) => e.outboxId !== outboxId));
}

/** Downscale an image File to a small JPEG dataURL for background storage. */
export function makePhotoThumbnail(file, maxDim = 320) {
  return new Promise((resolve) => {
    try {
      if (!file || !String(file.type || '').startsWith('image/')) return resolve(null);
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        try {
          const scale = Math.min(1, maxDim / Math.max(img.width, img.height));
          const w = Math.max(1, Math.round(img.width * scale));
          const h = Math.max(1, Math.round(img.height * scale));
          const canvas = document.createElement('canvas');
          canvas.width = w;
          canvas.height = h;
          canvas.getContext('2d').drawImage(img, 0, 0, w, h);
          URL.revokeObjectURL(url);
          resolve(canvas.toDataURL('image/jpeg', 0.7));
        } catch {
          URL.revokeObjectURL(url);
          resolve(null);
        }
      };
      img.onerror = () => { URL.revokeObjectURL(url); resolve(null); };
      img.src = url;
    } catch {
      resolve(null);
    }
  });
}

/** SHA-256 hex of a File (mockup lane: real hash of local bytes, EXIF still mocked). */
export async function sha256File(file) {
  const buf = await file.arrayBuffer();
  if (crypto?.subtle?.digest) {
    const hash = await crypto.subtle.digest('SHA-256', buf);
    return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, '0')).join('');
  }
  let h1 = 0x811c9dc5;
  const bytes = new Uint8Array(buf.slice(0, 65536));
  for (const b of bytes) { h1 ^= b; h1 = Math.imul(h1, 0x01000193); }
  return `mock-${(h1 >>> 0).toString(16).padStart(8, '0')}-${file.size}`;
}

export async function getReportsQueue(status) {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  const res = await apiRequest(`/reports/queue${qs}`);
  return res.reports || [];
}

export async function submitReport(reportData) {
  const res = await apiRequest('/reports', {
    method: 'POST',
    body: JSON.stringify(reportData),
  });
  return res;
}
