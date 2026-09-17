import { apiRequest } from './api';

/**
 * Reports — LIVE SIH26001 (real /api/reports + /api/reports/queue?status=).
 * No mock fallback on 422 (validation) — only on network failure the caller may locally queue.
 *
 * Photo lane (contract A§4: bytes never committed, metadata-only):
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

/**
 * SHA-256 hex of a File — always the REAL hash of the local bytes.
 * crypto.subtle is unavailable on plain-HTTP LAN (judge phone hotspot),
 * so the fallback is a pure-JS SHA-256 (same digest, no WebCrypto needed).
 * EXIF GPS is read from the file when present, else null (labeled in UI).
 */
function sha256Sync(bytes) {
  const K = [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2];
  let h0 = 0x6a09e667, h1 = 0xbb67ae85, h2 = 0x3c6ef372, h3 = 0xa54ff53a;
  let h4 = 0x510e527f, h5 = 0x9b05688c, h6 = 0x1f83d9ab, h7 = 0x5be0cd19;
  const bitLen = bytes.length * 8;
  const padded = new Uint8Array((((bytes.length + 8) >> 6) + 1) << 6);
  padded.set(bytes);
  padded[bytes.length] = 0x80;
  const dv = new DataView(padded.buffer);
  dv.setUint32(padded.length - 4, bitLen >>> 0, false);
  dv.setUint32(padded.length - 8, Math.floor(bitLen / 0x100000000), false);
  const w = new Int32Array(64);
  const rotr = (x, n) => (x >>> n) | (x << (32 - n));
  for (let off = 0; off < padded.length; off += 64) {
    for (let i = 0; i < 16; i++) w[i] = dv.getInt32(off + i * 4, false);
    for (let i = 16; i < 64; i++) {
      const s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3);
      const s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10);
      w[i] = (w[i - 16] + s0 + w[i - 7] + s1) | 0;
    }
    let [a, b, c, d, e, f, g, h] = [h0, h1, h2, h3, h4, h5, h6, h7];
    for (let i = 0; i < 64; i++) {
      const S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
      const ch = (e & f) ^ (~e & g);
      const t1 = (h + S1 + ch + K[i] + w[i]) | 0;
      const S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
      const mj = (a & b) ^ (a & c) ^ (b & c);
      const t2 = (S0 + mj) | 0;
      h = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0;
    }
    h0 = (h0 + a) | 0; h1 = (h1 + b) | 0; h2 = (h2 + c) | 0; h3 = (h3 + d) | 0;
    h4 = (h4 + e) | 0; h5 = (h5 + f) | 0; h6 = (h6 + g) | 0; h7 = (h7 + h) | 0;
  }
  return [h0, h1, h2, h3, h4, h5, h6, h7].map((x) => (x >>> 0).toString(16).padStart(8, '0')).join('');
}

/**
 * Device GPS from a JPEG file's EXIF (APP1/TIFF, GPS IFD) — real coordinates
 * or null. PNG/WebP/MP4 return null (no EXIF-GPS parse attempted); callers
 * must send null exif (backend skips the mismatch check) and say so in UI.
 * Never synthesize coordinates.
 */
export async function readExifGps(file) {
  try {
    if (file.type !== 'image/jpeg') return null;
    const buf = new Uint8Array(await file.arrayBuffer());
    if (buf[0] !== 0xff || buf[1] !== 0xd8) return null;
    let off = 2;
    while (off + 4 < buf.length) {
      if (buf[off] !== 0xff) break;
      const marker = buf[off + 1];
      const len = (buf[off + 2] << 8) | buf[off + 3];
      if (marker === 0xe1) {
        const gps = parseExifGps(buf.subarray(off + 4, off + 2 + len));
        if (gps) return gps;
      }
      if (marker === 0xda || marker === 0xd9) break;
      off += 2 + len;
    }
  } catch { /* fall through to null */ }
  return null;
}

function parseExifGps(seg) {
  try {
    if (String.fromCharCode(...seg.subarray(0, 6)) !== 'Exif\x00\x00') return null;
    const dv = new DataView(seg.buffer, seg.byteOffset, seg.byteLength);
    const tiff = 6;
    const le = String.fromCharCode(seg[tiff], seg[tiff + 1]) === 'II';
    if (!le && String.fromCharCode(seg[tiff], seg[tiff + 1]) !== 'MM') return null;
    const u16 = (o) => dv.getUint16(tiff + o, le);
    const u32 = (o) => dv.getUint32(tiff + o, le);
    if (u16(2) !== 42) return null;
    const ifd = (base) => {
      const n = u16(base);
      const out = {};
      for (let i = 0; i < n; i++) {
        const e = base + 2 + i * 12;
        out[u16(e)] = { type: u16(e + 2), count: u32(e + 4), val: u32(e + 8) };
      }
      return out;
    };
    const rat = (o) => {
      const num = new DataView(seg.buffer, seg.byteOffset).getUint32(tiff + o, le);
      const den = new DataView(seg.buffer, seg.byteOffset).getUint32(tiff + o + 4, le);
      return den === 0 ? NaN : num / den;
    };
    const ifd0 = ifd(u32(4));
    if (!(0x8825 in ifd0)) return null;
    const gps = ifd(ifd0[0x8825].val);
    const str = (e) => {
      const o = e.val;
      let s = '';
      for (let i = 0; i < e.count - 1; i++) s += String.fromCharCode(seg[tiff + o + i]);
      return s;
    };
    const dms = (e) => rat(e.val) + rat(e.val + 8) / 60 + rat(e.val + 16) / 3600;
    if (!(0 in gps) || !(2 in gps) || !(1 in gps) || !(4 in gps)) return null;
    let lat = dms(gps[2]);
    let lon = dms(gps[4]);
    if (str(gps[0]) === 'S') lat = -lat;
    if (str(gps[1]) === 'W') lon = -lon;
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) return null;
    return { lat, lon };
  } catch {
    return null;
  }
}

export async function sha256File(file) {
  const buf = await file.arrayBuffer();
  if (crypto?.subtle?.digest) {
    const hash = await crypto.subtle.digest('SHA-256', buf);
    return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, '0')).join('');
  }
  return sha256Sync(new Uint8Array(buf));
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
