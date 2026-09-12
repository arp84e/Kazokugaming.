// noticias.js
// Carga noticias REALES de videojuegos y las muestra como titular + imagen +
// resumen corto + enlace al artículo original. Nunca reproduce el artículo
// completo: esto es el mismo patrón que usa cualquier agregador de noticias
// (Google News, Feedly, Apple News...) y por diseño evita problemas de
// derechos de autor, siempre que se mantenga así — no ampliar los resúmenes
// ni quitar el enlace/atribución.
//
// Fuentes:
//   1. Búsqueda de Google Noticias en español ("videojuegos"): agrega
//      automáticamente artículos de múltiples medios hispanohablantes
//      (MeriStation, Vandal, HobbyConsolas, Xataka, etc.) sin que tengamos
//      que adivinar la URL de RSS exacta de cada uno — cada resultado enlaza
//      al medio original.
//   2. IGN (feed oficial en inglés): referencia internacional adicional.
//
// Usa el servicio gratuito rss2json.com como puente, porque los navegadores no
// pueden leer XML de RSS directamente por las políticas de CORS de la mayoría
// de sitios de noticias. Es un servicio de terceros ajeno a Anthropic/Firebase;
// si en el futuro deja de funcionar, ver SETUP.md para alternativas.

const FEEDS_NOTICIAS = [
    {
        url: 'https://news.google.com/rss/search?q=videojuegos&hl=es-419&gl=US&ceid=US:es-419',
        fuente: 'Google Noticias',
        color: 'bg-emerald-600',
        max: 4,
        esGoogleNews: true // el título trae " - NombreDelMedio" al final; lo separamos
    },
    { url: 'https://feeds.ign.com/ign/all', fuente: 'IGN', color: 'bg-indigo-600', max: 2 }
];

const RSS2JSON_ENDPOINT = 'https://api.rss2json.com/v1/api.json?rss_url=';
const CLAVE_CACHE = 'kazoku_noticias_cache_v2';
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

// Google Noticias pone el nombre del medio al final del título, separado por
// " - " (p. ej. "Se anuncia la secuela de X - MeriStation"). Lo separamos
// para mostrar un titular limpio y una insignia con el medio real.
function separarFuenteDeGoogleNews(tituloCrudo) {
    const idx = tituloCrudo.lastIndexOf(' - ');
    if (idx === -1) return { titulo: tituloCrudo, fuente: 'Google Noticias' };
    return {
        titulo: tituloCrudo.slice(0, idx).trim(),
        fuente: tituloCrudo.slice(idx + 3).trim() || 'Google Noticias'
    };
}

async function cargarFeed(feed) {
    const resp = await fetch(RSS2JSON_ENDPOINT + encodeURIComponent(feed.url));
    if (!resp.ok) throw new Error(`rss2json respondió ${resp.status} para ${feed.fuente}`);
    const data = await resp.json();
    if (data.status !== 'ok' || !Array.isArray(data.items)) throw new Error(`Feed inválido: ${feed.fuente}`);

    return data.items.slice(0, feed.max || 3).map((item) => {
        let titulo = (item.title || '').trim();
        let fuente = feed.fuente;

        if (feed.esGoogleNews) {
            const separado = separarFuenteDeGoogleNews(titulo);
            titulo = separado.titulo;
            fuente = separado.fuente;
        }

        return {
            titulo,
            resumen: limpiarYRecortar(item.description, 140),
            link: item.link,
            imagen: esUrlHttpsValida(item.thumbnail) ? item.thumbnail : (esUrlHttpsValida(item.enclosure?.link) ? item.enclosure.link : null),
            fuente,
            color: feed.color,
            fecha: item.pubDate ? new Date(item.pubDate).getTime() : 0
        };
    });
}

/**
 * Devuelve una lista de noticias reales de videojuegos (título, resumen corto,
 * imagen y enlace al artículo original), combinando varias fuentes.
 * Usa caché en sessionStorage para no golpear el servicio de terceros en
 * cada recarga de página.
 */
export async function cargarNoticias() {
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

    const resultados = await Promise.allSettled(FEEDS_NOTICIAS.map(cargarFeed));

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

