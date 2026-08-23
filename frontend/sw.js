const CACHE_NAME = 'wacrm-v1';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  'https://cdn.tailwindcss.com',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)).then(()=> self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=> caches.delete(k)))).then(()=> self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  // Network first for API, cache first for assets
  if (req.url.includes('/api/') || req.url.includes('localhost:8000')) {
    event.respondWith(
      fetch(req).catch(()=> caches.match(req))
    );
    return;
  }
  event.respondWith(
    caches.match(req).then(cached => {
      if (cached) return cached;
      return fetch(req).then(res => {
        // cache successful GET
        if (res.ok && req.method==='GET') {
          const clone = res.clone();
          caches.open(CACHE_NAME).then(c=> c.put(req, clone));
        }
        return res;
      }).catch(()=> {
        // offline fallback for navigation
        if (req.mode==='navigate') return caches.match('./index.html');
      });
    })
  );
});
