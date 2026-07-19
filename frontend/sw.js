/* ═══════════════════════════════════════════════════════════════════
   MediScan AI — Service Worker (Workbox-free, manual caching)
   ═══════════════════════════════════════════════════════════════════ */

const CACHE_NAME = "mediscan-v1";

// ── Assets to pre-cache on install ───────────────────────────────
const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./css/style.css",
  "./js/app.js",
  "./manifest.json",
  "./icons/icon-72.png",
  "./icons/icon-96.png",
  "./icons/icon-128.png",
  "./icons/icon-144.png",
  "./icons/icon-152.png",
  "./icons/icon-192.png",
  "./icons/icon-384.png",
  "./icons/icon-512.png",
];

// ── Install: pre-cache core assets ───────────────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_URLS);
    }),
  );
  self.skipWaiting();
});

// ── Activate: clean old caches ───────────────────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name)),
      );
    }),
  );
  self.clients.claim();
});

// ── Fetch: cache-first for static, network-first for API ─────────
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // ── API calls: network-first, fallback to cache ────────────────
  if (url.pathname === "/analyze" || url.pathname.startsWith("/api/")) {
    event.respondWith(networkFirst(request));
    return;
  }

  // ── Static assets: cache-first ─────────────────────────────────
  event.respondWith(cacheFirst(request));
});

// ── Cache-first strategy ─────────────────────────────────────────
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response && response.status === 200 && response.type === "basic") {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    // Offline fallback for navigation requests
    if (request.mode === "navigate") {
      return caches.match("./");
    }
    return new Response("Offline", { status: 503 });
  }
}

// ── Network-first strategy ───────────────────────────────────────
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response && response.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(
      JSON.stringify({
        error: "You are offline. Please check your connection and try again.",
      }),
      {
        status: 503,
        headers: { "Content-Type": "application/json" },
      },
    );
  }
}
