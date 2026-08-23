const CACHE_NAME = 'wacrm-landing-v1';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png'
];
self.addEventListener('install', e=>{
  e.waitUntil(caches.open(CACHE_NAME).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate', e=>{
  e.waitUntil(caches.keys().then(keys=> Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k)))) .then(()=>self.clients.claim()));
});
self.addEventListener('fetch', e=>{
  e.respondWith(caches.match(e.request).then(cached=> cached || fetch(e.request).then(res=>{
    if(res.ok && e.request.method==='GET'){ const clone=res.clone(); caches.open(CACHE_NAME).then(c=>c.put(e.request, clone)); }
    return res;
  }).catch(()=> e.request.mode==='navigate' ? caches.match('./index.html') : null)));
});
