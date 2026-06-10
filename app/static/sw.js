// Mishra Travel Hub — Service Worker
// Phase 9: Offline-first caching with offline session security

const CACHE_VERSION  = 'v10';
const STATIC_CACHE   = `mth-static-${CACHE_VERSION}`;
const PAGES_CACHE    = `mth-pages-${CACHE_VERSION}`;
const MEDIA_CACHE    = `mth-media-${CACHE_VERSION}`;
const SESSION_CACHE  = 'mth-session';            // unversioned — survives SW updates
const SESSION_KEY    = '/__mth-offline-session__';
const OFFLINE_URL    = '/static/offline.html';
const LOCK_URL       = '/static/offline-lock.html';

// Static assets pre-cached on install (guaranteed offline availability)
const PRECACHE_URLS = [
  '/static/css/app.css',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/images/family-hero.jpeg',
  OFFLINE_URL,
  LOCK_URL,
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
// ACTIVATE — purge stale caches (session cache is kept across versions)
// ---------------------------------------------------------------------------
self.addEventListener('activate', (event) => {
  const keep = [STATIC_CACHE, PAGES_CACHE, MEDIA_CACHE, SESSION_CACHE];
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => !keep.includes(k)).map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ---------------------------------------------------------------------------
// Offline session marker — cache-based because SW cannot read localStorage
// ---------------------------------------------------------------------------
async function setOfflineSession() {
  const cache = await caches.open(SESSION_CACHE);
  await cache.put(SESSION_KEY, new Response('1'));
}

async function clearOfflineSession() {
  const cache = await caches.open(SESSION_CACHE);
  await cache.delete(SESSION_KEY);
}

async function hasOfflineSession() {
  const cache = await caches.open(SESSION_CACHE);
  const hit = await cache.match(SESSION_KEY);
  return Boolean(hit);
}

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

  // Local static assets — cache-first, public shell (CSS, icons, lock page)
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }

  // Uploaded memory photos — private media, cleared on logout
  if (url.pathname.startsWith('/media/')) {
    event.respondWith(cacheFirst(request, MEDIA_CACHE));
    return;
  }

  // Auth pages — network only, never cached as pages.
  // Offline: login is impossible anyway, show the lock screen.
  if (url.pathname.startsWith('/auth/')) {
    if (request.headers.get('Accept')?.includes('text/html')) {
      event.respondWith(
        fetch(request).catch(() => caches.match(LOCK_URL))
      );
    }
    return;
  }

  // HTML navigation pages (private app content):
  // Network-first; offline fallback is gated by the offline session marker
  if (request.headers.get('Accept')?.includes('text/html')) {
    event.respondWith(networkFirstHtml(request));
    return;
  }
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
    // OFFLINE: only serve private cached pages with a valid offline session
    if (await hasOfflineSession()) {
      const cached = await cache.match(request);
      return cached || (await caches.match(OFFLINE_URL));
    }
    return caches.match(LOCK_URL);
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
// Messages from the app
//   MTH_AUTH   — authenticated page loaded → set offline session marker
//   MTH_LOGOUT — user logged out → clear marker + private caches
// ---------------------------------------------------------------------------
self.addEventListener('message', (event) => {
  const type = event.data?.type;
  if (type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (type === 'MTH_AUTH') {
    event.waitUntil(setOfflineSession());
  } else if (type === 'MTH_LOGOUT') {
    event.waitUntil(Promise.all([
      clearOfflineSession(),
      caches.delete(PAGES_CACHE),
      caches.delete(MEDIA_CACHE),
    ]));
  }
});
