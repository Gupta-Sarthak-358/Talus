/**
 * Photo screening measurements (real computation, honest limits).
 *
 * analyzePhoto() measures three quantities on the attached report photo in
 * the browser (canvas, downscaled ≤320px): Sobel edge density, dark-pixel
 * fraction, and Laplacian-variance sharpness. These are MEASUREMENTS for the
 * reviewing officer — not a diagnosis. There is no crack/no-crack verdict
 * because no detector has been trained or calibrated on Himalayan slope
 * imagery, and inventing thresholds would be fabrication.
 *
 * Video files: unsupported (returns supported:false), stated, not faked.
 */

function luminance(r, g, b) {
  return 0.299 * r + 0.587 * g + 0.114 * b;
}

export async function analyzePhoto(file) {
  if (!file || !String(file.type || '').startsWith('image/')) {
    return { supported: false, reason: 'Screening runs on photos only, not video.' };
  }
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, 320 / Math.max(bitmap.width, bitmap.height));
  const w = Math.max(1, Math.round(bitmap.width * scale));
  const h = Math.max(1, Math.round(bitmap.height * scale));
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(bitmap, 0, 0, w, h);
  if (typeof bitmap.close === 'function') bitmap.close();
  const px = ctx.getImageData(0, 0, w, h).data;

  const gray = new Float32Array(w * h);
  let dark = 0;
  for (let i = 0; i < w * h; i++) {
    const g = luminance(px[i * 4], px[i * 4 + 1], px[i * 4 + 2]);
    gray[i] = g;
    if (g < 60) dark++;
  }

  // Sobel edge magnitude + Laplacian variance in one interior pass
  let edges = 0;
  let lapSum = 0;
  let lapSq = 0;
  let n = 0;
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const i = y * w + x;
      const gx = -gray[i - w - 1] - 2 * gray[i - 1] - gray[i + w - 1]
        + gray[i - w + 1] + 2 * gray[i + 1] + gray[i + w + 1];
      const gy = -gray[i - w - 1] - 2 * gray[i - w] - gray[i - w + 1]
        + gray[i + w - 1] + 2 * gray[i + w] + gray[i + w + 1];
      if (Math.hypot(gx, gy) > 100) edges++;
      const lap = 4 * gray[i] - gray[i - 1] - gray[i + 1] - gray[i - w] - gray[i + w];
      lapSum += lap;
      lapSq += lap * lap;
      n++;
    }
  }
  const mean = lapSum / Math.max(1, n);
  const sharpness = lapSq / Math.max(1, n) - mean * mean;

  return {
    supported: true,
    width: bitmap.width,
    height: bitmap.height,
    sampled: `${w}×${h}`,
    edgeDensityPct: Math.round((edges / Math.max(1, n)) * 1000) / 10,
    darkFractionPct: Math.round((dark / (w * h)) * 1000) / 10,
    sharpness: Math.round(sharpness * 10) / 10,
    measuredAt: new Date().toISOString(),
  };
}
