/* Aventura Anabellei — service worker.
   Pagina: network-first, ca sa prinda versiunile noi imediat, cu revenire
   la cache cand nu e internet. Restul: cache-first, sunt fisiere care nu
   se schimba decat la un deploy nou (si atunci se schimba VERSION). */

const VERSION = 'v3';
const CACHE   = 'anabelle-' + VERSION;

const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './apple-touch-icon.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-512-maskable.png'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if(req.method !== 'GET') return;

  const isDoc = req.mode === 'navigate' || req.destination === 'document';
  const isFont = /fonts\.(googleapis|gstatic)\.com/.test(req.url);
  const sameOrigin = new URL(req.url).origin === self.location.origin;

  if(isDoc){
    e.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put('./index.html', copy));
          return res;
        })
        .catch(() => caches.match('./index.html').then(r => r || caches.match('./')))
    );
    return;
  }

  if(sameOrigin || isFont){
    e.respondWith(
      caches.match(req).then(hit => {
        if(hit) return hit;
        return fetch(req).then(res => {
          if(res && (res.ok || res.type === 'opaque')){
            const copy = res.clone();
            caches.open(CACHE).then(c => c.put(req, copy));
          }
          return res;
        });
      })
    );
  }
});
