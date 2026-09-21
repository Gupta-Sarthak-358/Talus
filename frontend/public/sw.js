/* TALUS service worker v2 — network-first shell + cache-first hashed chunks.
 * Shell (/, /index.html) is network-first so HTML always matches deployed
 * chunk hashes (old-tab/new-deploy 404 impossible). Hashed /assets chunks are
 * immutable: cache-first, safe forever. /api is network-only.
 * Bump CACHE when shipping a new demo build (byte change triggers SW update).
 */
const CACHE = 'talus-shell-v4-netfirst-shell';
const SHELL = ['/', '/index.html', '/favicon.svg', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  // Live API/data: network only (offline shows the app's own offline badge).
  if (url.pathname.startsWith('/api')) return;
  // App shell: network-first — stale HTML referencing purged chunk hashes
  // is what crashed old tabs on redeploy. Offline falls back to cache.
  if (url.pathname === '/' || url.pathname === '/index.html') {
    event.respondWith(
      fetch(request)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((cache) => cache.put(request, copy));
          }
          return res;
        })
        .catch(() => caches.match(request).then((hit) => {
          if (hit) return hit;
          return new Response('TALUS offline', { status: 503 });
        }))
    );
    return;
  }
  // Hashed chunks + static: cache-first, then network with cache fill.
  // Never reject: offline + miss returns 503, not a thrown promise.
  event.respondWith(
    caches.match(request).then(
      (hit) =>
        hit ||
        fetch(request)
          .then((res) => {
            if (url.origin === self.location.origin && res.ok) {
              const copy = res.clone();
              caches.open(CACHE).then((cache) => cache.put(request, copy));
            }
            return res;
          })
          .catch(() => new Response('TALUS offline', { status: 503 }))
    )
  );
});
