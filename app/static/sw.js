// Mishra Travel Hub — Service Worker
// Phase 2 scaffold. Offline caching will be added in a future phase.

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim());
});
