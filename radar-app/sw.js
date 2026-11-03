// Radar Emploi Nature — hors connexion.
// La page et la liste des offres sont d'abord demandées au réseau (pour avoir les nouvelles offres),
// sinon la dernière copie enregistrée est utilisée. Les icônes viennent du cache.
const CACHE = "radar-v1";
const SHELL = ["./", "manifest.webmanifest", "icons/apple-touch-icon.png", "icons/icon-192.png", "icons/icon-512.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("radar-") && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  // Le sous-dossier expositions/ a son propre service worker.
  if (url.pathname.includes("/expositions/")) return;
  const networkFirst = url.pathname.endsWith("/") || url.pathname.endsWith(".html") || url.pathname.endsWith(".json");
  if (networkFirst) {
    e.respondWith(fetch(e.request).then(r => { if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); } return r; })
      .catch(() => caches.match(e.request, { ignoreSearch: true })));
  } else {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
  }
});
