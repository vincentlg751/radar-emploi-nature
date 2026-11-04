// Hors connexion : l'application est servie depuis le cache ; la liste des expositions
// est d'abord demandée au réseau (pour voir les nouvelles), sinon la dernière copie est utilisée.
const CACHE = "expos-v5";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icons/apple-touch-icon.png", "icons/icon-192.png", "vendor/leaflet.js", "vendor/leaflet.css"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("expos-") && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  const networkFirst = url.pathname.endsWith(".json") || url.pathname.endsWith("/") || url.pathname.endsWith(".html");
  if (networkFirst) {
    e.respondWith(fetch(e.request).then(r => { if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); } return r; })
      .catch(() => caches.match(e.request, { ignoreSearch: true })));
  } else {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
  }
});
