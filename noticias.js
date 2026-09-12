// noticias.js
// Carga noticias REALES de videojuegos desde los feeds RSS oficiales de medios
// reconocidos (IGN, Kotaku) y las muestra como titular + imagen + resumen corto
// + enlace al artículo original. Nunca reproduce el artículo completo: esto es
// el mismo patrón que usa cualquier agregador de noticias (Google News, Feedly,
// Apple News...) y por diseño evita problemas de derechos de autor, siempre que
// se mantenga así — no ampliar los resúmenes ni quitar el enlace/atribución.
//
// Usa el servicio gratuito rss2json.com como puente, porque los navegadores no
// pueden leer XML de RSS directamente por las políticas de CORS de la mayoría
// de sitios de noticias. Es un servicio de terceros ajeno a Anthropic/Firebase;
// si en el futuro deja de funcionar, ver SETUP.md para alternativas.

const FEEDS_NOTICIAS = [
    { url: 'https://feeds.ign.com/ign/all', fuente: 'IGN', color: 'bg-indigo-600' },
    { url: 'https://kotaku.com/rss', fuente: 'Kotaku', color: 'bg-fuchsia-600' }
];

const RSS2JSON_ENDPOINT = 'https://api.rss2json.com/v1/api.json?rss_url=';
const CLAVE_CACHE = 'kazoku_noticias_cache_v1';
const DURACION_CACHE_MS = 20 * 60 * 1000; // 20 minutos

function limpiarYRecortar(html, maxLen) {
    const div = document.createElement('div');
    div.innerHTML = html || '';
    let texto = (div.textContent || div.innerText || '').replace(/\s+/g, ' ').trim();
    if (texto.length > maxLen) texto = texto.slice(0, maxLen).trim() + '…';
    return texto;
}

function esUrlHttpsValida(url) {
    try {
        const u = new URL(url);
        return u.protocol === 'https:';
    } catch {
        return false;
    }
}

async function cargarFeed(feed, maxItems) {
    const resp = await fetch(RSS2JSON_ENDPOINT + encodeURIComponent(feed.url));
    if (!resp.ok) throw new Error(`rss2json respondió ${resp.status} para ${feed.fuente}`);
    const data = await resp.json();
    if (data.status !== 'ok' || !Array.isArray(data.items)) throw new Error(`Feed inválido: ${feed.fuente}`);

    return data.items.slice(0, maxItems).map((item) => ({
        titulo: (item.title || '').trim(),
        resumen: limpiarYRecortar(item.description, 140),
        link: item.link,
        imagen: esUrlHttpsValida(item.thumbnail) ? item.thumbnail : (esUrlHttpsValida(item.enclosure?.link) ? item.enclosure.link : null),
        fuente: feed.fuente,
        color: feed.color,
        fecha: item.pubDate ? new Date(item.pubDate).getTime() : 0
    }));
}

/**
 * Devuelve una lista de noticias reales de videojuegos (título, resumen corto,
 * imagen y enlace al artículo original), combinando varias fuentes.
 * Usa caché en sessionStorage para no golpear el servicio de terceros en
 * cada recarga de página.
 */
export async function cargarNoticias(maxPorFuente = 3) {
    try {
        const cacheRaw = sessionStorage.getItem(CLAVE_CACHE);
        if (cacheRaw) {
            const cache = JSON.parse(cacheRaw);
            if (Date.now() - cache.timestamp < DURACION_CACHE_MS && Array.isArray(cache.noticias) && cache.noticias.length > 0) {
                return cache.noticias;
            }
        }
    } catch {
        // caché corrupta o no disponible: seguimos con la carga normal
    }

    const resultados = await Promise.allSettled(
        FEEDS_NOTICIAS.map((feed) => cargarFeed(feed, maxPorFuente))
    );

    const noticias = resultados
        .filter((r) => r.status === 'fulfilled')
        .flatMap((r) => r.value)
        .filter((n) => n.titulo && n.link)
        .sort((a, b) => b.fecha - a.fecha);

    if (noticias.length > 0) {
        try {
            sessionStorage.setItem(CLAVE_CACHE, JSON.stringify({ timestamp: Date.now(), noticias }));
        } catch {
            // sessionStorage llena o bloqueada: no es crítico, simplemente no cacheamos
        }
    }

    return noticias;
}
