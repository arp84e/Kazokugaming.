// sw.js
// Service Worker de KazokuGaming.
//
// Qué SÍ cachea: el "shell" estático de la app (HTML, JS propio, íconos) para
// que abrir el sitio sea instantáneo y funcione incluso con conexión pobre.
//
// Qué NO cachea: nada de Firebase (Auth/Firestore) ni Tailwind/Google Fonts/
// rss2json — todo eso sigue yendo directo a la red, porque es contenido que
// cambia todo el tiempo (torneos, chats, noticias) y cachearlo mal mostraría
// información vieja como si fuera actual.
//
// Estrategia: "network-first, con respaldo en caché". Es decir: intenta
// siempre traer la versión más nueva de internet; si no hay conexión, usa lo
// que haya guardado. Así nunca se ve una versión vieja teniendo internet.

const VERSION = 'kazoku-v1';
const ARCHIVOS_SHELL = [
    'index.html',
    'grupos.html',
    'torneos.html',
    'login.html',
    'perfil.html',
    'usuario.html',
    '404.html',
    'header.js',
    'firebase-init.js',
    'ui-utils.js',
    'noticias.js',
    'manifest.json',
    'icons/icon-192.png',
    'icons/icon-512.png'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(VERSION).then((cache) => cache.addAll(ARCHIVOS_SHELL).catch(() => {
            // Si algún archivo falla (p. ej. todavía no existe en este despliegue),
            // no bloqueamos la instalación del Service Worker por eso.
        }))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((claves) =>
            Promise.all(claves.filter((c) => c !== VERSION).map((c) => caches.delete(c)))
        )
    );
    self.clients.claim();
});

// Dominios que NUNCA se deben servir desde caché (datos siempre en vivo)
const DOMINIOS_SIEMPRE_RED = [
    'firestore.googleapis.com',
    'identitytoolkit.googleapis.com',
    'securetoken.googleapis.com',
    'firebaseapp.com',
    'api.rss2json.com',
    'news.google.com',
    'feeds.ign.com',
    'kotaku.com'
];

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Solo interceptamos peticiones GET del mismo origen (nuestros propios archivos).
    // Todo lo demás (Firebase, CDNs, feeds de noticias) pasa directo a la red.
    if (event.request.method !== 'GET') return;
    if (url.origin !== self.location.origin) return;
    if (DOMINIOS_SIEMPRE_RED.some((d) => url.hostname.includes(d))) return;

    event.respondWith(
        fetch(event.request)
            .then((respuesta) => {
                const copia = respuesta.clone();
                caches.open(VERSION).then((cache) => cache.put(event.request, copia));
                return respuesta;
            })
            .catch(() => caches.match(event.request).then((r) => r || caches.match('index.html')))
    );
});
