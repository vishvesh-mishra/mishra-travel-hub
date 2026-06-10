// Mishra Travel Hub — Service Worker
// Phase 6A: Full offline-first caching strategy

const CACHE_VERSION  = 'v8';
const STATIC_CACHE   = `mth-static-${CACHE_VERSION}`;
const PAGES_CACHE    = `mth-pages-${CACHE_VERSION}`;
const OFFLINE_URL    = '/static/offline.html';

// Static assets pre-cached on install (guaranteed offline availability)
const PRECACHE_URLS = [
  '/static/css/app.css',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/images/family-hero.jpeg',
  OFFLINE_URL,
];

// ---------------------------------------------------------------------------
// INSTALL — pre-cache static shell
// ---------------------------------------------------------------------------
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

// ---------------------------------------------------------------------------
// ACTIVATE — purge stale caches
// ---------------------------------------------------------------------------
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== STATIC_CACHE && k !== PAGES_CACHE)
          .map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ---------------------------------------------------------------------------
// FETCH — tiered caching strategy
// ---------------------------------------------------------------------------
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle GET requests
  if (request.method !== 'GET') return;

  // CDN resources (Bootstrap, fonts, Bootstrap Icons):
  // Stale-while-revalidate — serve cached immediately, refresh in background
  if (url.origin !== self.location.origin) {
    event.respondWith(staleWhileRevalidate(request, STATIC_CACHE));
    return;
  }

  // Local static assets (/static/…) and uploaded memory photos (/media/…):
  // Cache-first — filenames are immutable (uuid), only fetch when cache is cold
  if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }

  // HTML navigation pages:
  // Network-first with cache fallback, offline page as last resort
  if (request.headers.get('Accept')?.includes('text/html')) {
    event.respondWith(networkFirstHtml(request));
    return;
  }

  // Everything else (API calls, form POSTs already excluded above):
  // Network only
});

// ---------------------------------------------------------------------------
// Strategy helpers
// ---------------------------------------------------------------------------

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (_) {
    return caches.match(OFFLINE_URL);
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache  = await caches.open(cacheName);
  const cached = await cache.match(request);

  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) cache.put(request, response.clone());
    return response;
  }).catch(() => cached);

  return cached || fetchPromise;
}

async function networkFirstHtml(request) {
  const cache = await caches.open(PAGES_CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (_) {
    const cached = await cache.match(request);
    return cached || (await caches.match(OFFLINE_URL));
  }
}

// ---------------------------------------------------------------------------
// Background sync — notify clients to process their localStorage queue
// ---------------------------------------------------------------------------
self.addEventListener('sync', (event) => {
  if (event.tag === 'mth-sync') {
    event.waitUntil(notifyClients());
  }
});

async function notifyClients() {
  const all = await self.clients.matchAll({ includeUncontrolled: true });
  all.forEach((client) => client.postMessage({ type: 'MTH_SYNC' }));
}

// ---------------------------------------------------------------------------
// Message handler — client can request cache purge for fresh install
// ---------------------------------------------------------------------------
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
});
