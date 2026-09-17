/* One-call service-worker registration. Safe no-op when SW unsupported
 * or registration fails (private mode, file://, preview without SW). */

export function registerPWA() {
  try {
    if (!('serviceWorker' in navigator)) return;
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        /* offline demo must never crash on SW failure */
      });
    });
  } catch {
    /* ignore */
  }
}
