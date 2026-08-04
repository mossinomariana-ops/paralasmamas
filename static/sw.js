/* =========================================================================
   Service worker de la PWA "Lactancia".
   Objetivo: app instalable y carga rápida, SIN servir datos viejos.
     - /api/*      -> siempre red (nunca cache); sin conexión, error.
     - navegación  -> red primero; si falla, cache y luego pantalla offline.
     - /static/*   -> cache primero con refresco en segundo plano (los
                      archivos llevan ?v=<version>, así un cambio se re-baja).
   ========================================================================= */

// v4: se rehízo el ícono maskable para la app de Google Play. CONSERVA EL MISMO
// NOMBRE de archivo, así que las mamás que ya usan la app lo tienen guardado en
// la caché de abajo: sin subir este número seguirían viendo el ícono viejo, el
// que Android recortaba mal.
const VERSION = 'lac-v4';
const SHELL_CACHE = 'lac-shell-' + VERSION;
const RUNTIME_CACHE = 'lac-runtime-' + VERSION;

// Acá van SOLO los archivos que se piden con la dirección pelada, sin el `?v=`
// del final (los íconos, que los pide el manifiesto). El resto de los estáticos
// —style.css, lactancia.js y ahora también el calendario— viajan con `?v=` y se
// guardan solos en la caché de abajo la primera vez que la app abre con
// internet. Poner acá una dirección sin `?v=` guardaría una copia que después
// nadie encuentra, porque la búsqueda es por dirección exacta.
//
// Las capturas de pantalla de la tienda NO van acá: pesan más de un mega, solo
// las mira la pantalla de instalación, y `addAll` es todo o nada (si una sola
// fallara, no se instalaría el service worker entero).
const PRECACHE = [
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/icon-512-maskable.png',
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

  // Esta dirección la consulta ANDROID para verificar que la app de la tienda
  // es nuestra. Nunca se guarda ni se toca: una respuesta vieja acá haría que la
  // app abriera con la barra del navegador arriba. Hoy ya quedaría afuera de las
  // tres ramas de abajo, pero conviene dejarlo escrito por si algún día alguien
  // agrega un "guardemos todo".
  if (url.pathname.startsWith('/.well-known/')) return;

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
