/** Service worker mínimo — shell offline do painel */
const CACHE = "maestro-painel-v1";
const PRECACHE = [
  "./",
  "./index.html",
  "./styles.css",
  "./config.js",
  "./ui.js",
  "./charts.js",
  "./search.js",
  "./pwa.js",
  "./app.js",
  "./voice-core.js",
  "./voice.js",
  "./manifest.json",
  "./mapa-agentes.html",
  "./tasks.html",
  "./tasks-kanban.js",
  "./tasks-kanban.css",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE).catch(() => undefined))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api/")) {
    return;
  }
  if (event.request.method !== "GET") return;
  event.respondWith(
    fetch(event.request)
      .then((res) => {
        if (res.ok && url.origin === self.location.origin && url.pathname.startsWith("/painel")) {
          const clone = res.clone();
          caches.open(CACHE).then((c) => c.put(event.request, clone));
        }
        return res;
      })
      .catch(() => caches.match(event.request).then((r) => r || caches.match("./index.html")))
  );
});
