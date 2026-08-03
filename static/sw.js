/* =========================================================================
   Service worker de la PWA "Lactancia".
   Objetivo: app instalable y carga rápida, SIN servir datos viejos.
     - /api/*      -> siempre red (nunca cache); sin conexión, error.
     - navegación  -> red primero; si falla, cache y luego pantalla offline.
     - /static/*   -> cache primero con refresco en segundo plano (los
                      archivos llevan ?v=<version>, así un cambio se re-baja).
   ========================================================================= */

const VERSION = 'lac-v3';
const SHELL_CACHE = 'lac-shell-' + VERSION;
const RUNTIME_CACHE = 'lac-runtime-' + VERSION;

// Acá van SOLO los archivos que se piden con la dirección pelada, sin el `?v=`
// del final (los íconos, que los pide el manifiesto). El resto de los estáticos
// —style.css, lactancia.js y ahora también el calendario— viajan con `?v=` y se
// guardan solos en la caché de abajo la primera vez que la app abre con
// internet. Poner acá una dirección sin `?v=` guardaría una copia que después
// nadie encuentra, porque la búsqueda es por dirección exacta.
const PRECACHE = [
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== SHELL_CACHE && k !== RUNTIME_CACHE)
            .map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  // Todo lo que pide la app es nuestro. Si algún día vuelve a haber algo de
  // afuera, esta línea lo deja pasar de largo sin tocarlo.
  //
  // Ojo al dato: ANTES el calendario venía de una web ajena y esta misma línea
  // lo dejaba afuera de la caché, por eso no andaba sin conexión. Al mudarlo
  // adentro de la app pasó a entrar por el camino de /static/ de más abajo y
  // ahora sí queda guardado.
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(req).catch(() => new Response(
        JSON.stringify({ ok: false, offline: true, error: 'Sin conexión' }),
        { status: 503, headers: { 'Content-Type': 'application/json' } }
      ))
    );
    return;
  }

  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).catch(() => caches.match(req).then((r) => r || offlineFallback()))
    );
    return;
  }

  // Los videos quedan FUERA de la caché: pesan varios MB y el navegador los
  // pide por pedacitos (respuestas 206), que la caché no sabe guardar.
  if (url.pathname.startsWith('/static/') && !/\.(mp4|webm|mov)$/i.test(url.pathname)) {
    event.respondWith(
      caches.open(RUNTIME_CACHE).then((cache) =>
        cache.match(req).then((cached) => {
          const network = fetch(req).then((resp) => {
            if (resp && resp.status === 200) cache.put(req, resp.clone());
            return resp;
          }).catch(() => cached);
          return cached || network;
        })
      )
    );
  }
});

function offlineFallback() {
  const html =
    '<!doctype html><html lang="es"><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width, initial-scale=1">' +
    '<title>Sin conexión</title>' +
    '<div style="font-family:system-ui,sans-serif;text-align:center;padding:3rem 1.5rem;color:#374151">' +
    '<div style="font-size:3rem">🍼</div>' +
    '<h1 style="font-size:1.25rem;margin:.5rem 0">Sin conexión</h1>' +
    '<p style="color:#6b7280">Necesitás internet para ver tus datos.<br>' +
    'Probá de nuevo cuando tengas señal.</p></div></html>';
  return new Response(html, {
    status: 200,
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
  });
}
