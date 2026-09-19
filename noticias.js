// noticias.js
// Carga noticias REALES de videojuegos y tecnología y las muestra como
// titular + imagen + resumen corto + enlace al artículo original. Nunca
// reproduce el artículo completo: esto es el mismo patrón que usa cualquier
// agregador de noticias (Google News, Feedly, Apple News...) y por diseño
// evita problemas de derechos de autor, siempre que se mantenga así — no
// ampliar los resúmenes ni quitar el enlace/atribución.
//
// Fuentes:
//   - Tecnología: Xataka (feed oficial confirmado, en español, CON imagen
//     real en cada noticia — feeds.weblogssl.com/xataka2).
//   - Videojuegos: IGN (feed oficial confirmado, con imagen real, pero en
//     inglés) + Google Noticias en español "videojuegos" (sin imagen
//     garantizada, pero en español) como complemento/respaldo.
//
// No pude confirmar con certeza un feed de un medio de videojuegos en
// español que garantice imagen en cada noticia (lo intenté con Vandal,
// 3DJuegos y HobbyConsolas sin éxito) — por eso Videojuegos combina ambas.
// Si el usuario confirma él mismo la URL de RSS de algún medio de
// videojuegos en español con imágenes, se puede agregar aquí fácilmente.
//
// Usa el servicio gratuito rss2json.com como puente, porque los navegadores no
// pueden leer XML de RSS directamente por las políticas de CORS de la mayoría
// de sitios de noticias. Es un servicio de terceros ajeno a Anthropic/Firebase;
// si en el futuro deja de funcionar, ver SETUP.md para alternativas.

function googleNewsRss(consulta) {
    return `https://news.google.com/rss/search?q=${encodeURIComponent(consulta)}&hl=es-419&gl=US&ceid=US:es-419`;
}

const FEEDS_NOTICIAS = [
    { url: 'http://feeds.weblogssl.com/xataka2', categoria: 'Tecnología', fuente: 'Xataka', color: 'bg-sky-600', max: 6 },
    { url: 'https://feeds.ign.com/ign/all', categoria: 'Videojuegos', fuente: 'IGN', color: 'bg-emerald-600', max: 4 },
    {
        url: googleNewsRss('videojuegos'),
        categoria: 'Videojuegos',
        fuente: 'Google Noticias',
        color: 'bg-emerald-600',
        max: 4,
        esGoogleNews: true // el título trae " - NombreDelMedio" al final; lo separamos
    }
];

const RSS2JSON_ENDPOINT = 'https://api.rss2json.com/v1/api.json?rss_url=';
const CLAVE_CACHE = 'kazoku_noticias_cache_v5';
const DURACION_CACHE_MS = 20 * 60 * 1000; // 20 minutos
const TIMEOUT_POR_FEED_MS = 8000; // si una fuente tarda más de 8s, la damos por perdida y seguimos con las demás

function limpiarYRecortar(html, maxLen) {
    const div = document.createElement('div');
    div.innerHTML = html || '';
    let texto = (div.textContent || div.innerText || '').replace(/\s+/g, ' ').trim();
    if (texto.length > maxLen) texto = texto.slice(0, maxLen).trim() + '…';
    return texto;
}

// Valida que una URL sea https:// y devuelve su forma NORMALIZADA (url.href),
// nunca la cadena original. Esto importa porque el constructor URL() acepta
// cadenas "raras" (p. ej. con una comilla incrustada) sin lanzar error, pero al
// normalizarlas esos caracteres quedan porcentaje-codificados — así, aunque el
// feed de un tercero (rss2json/Google Noticias/IGN) devolviera algo
// manipulado, nunca llega una comilla real al HTML.
function normalizarUrlHttpsOVacio(url) {
    try {
        const u = new URL(url);
        return u.protocol === 'https:' ? u.href : null;
    } catch {
        return null;
    }
}

// rss2json no siempre rellena "thumbnail"/"enclosure" aunque el HTML del
// resumen sí traiga una imagen incrustada (es el caso de Xataka: cada
// noticia empieza con <img src="...">). Como respaldo, buscamos la primera
// imagen dentro del HTML del resumen/contenido nosotros mismos.
function primeraImagenEnHtml(html) {
    if (!html) return null;
    const match = html.match(/<img[^>]+src=["']([^"']+)["']/i);
    return match ? match[1] : null;
}

function extraerImagen(item) {
    const candidatas = [
        item.thumbnail,
        item.enclosure && item.enclosure.link,
        primeraImagenEnHtml(item.content),
        primeraImagenEnHtml(item.description)
    ];
    for (const candidata of candidatas) {
        const normalizada = normalizarUrlHttpsOVacio(candidata);
        if (normalizada) return normalizada;
    }
    return null;
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

// Normaliza un título para poder comparar si dos noticias de fuentes
// distintas son "la misma historia" (mismo suceso cubierto por dos medios).
function normalizarTitulo(titulo) {
    return titulo
        .toLowerCase()
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // quita acentos
        .replace(/[^a-z0-9\s]/g, '') // quita puntuación
        .trim()
        .slice(0, 45); // comparamos solo el inicio: suele bastar para detectar la misma noticia
}

/**
 * Convierte un timestamp en milisegundos a texto relativo en español,
 * p. ej. "hace 2 horas", "hace 3 días". Si no hay Intl.RelativeTimeFormat
 * disponible (muy improbable en 2026) devuelve cadena vacía.
 */
export function formatearTiempoRelativo(timestampMs) {
    if (!timestampMs) return '';
    const diffSegundos = Math.round((timestampMs - Date.now()) / 1000);

    try {
        const rtf = new Intl.RelativeTimeFormat('es', { numeric: 'auto' });
        const abs = Math.abs(diffSegundos);
        if (abs < 60) return rtf.format(Math.round(diffSegundos), 'second');
        if (abs < 3600) return rtf.format(Math.round(diffSegundos / 60), 'minute');
        if (abs < 86400) return rtf.format(Math.round(diffSegundos / 3600), 'hour');
        if (abs < 604800) return rtf.format(Math.round(diffSegundos / 86400), 'day');
        return rtf.format(Math.round(diffSegundos / 604800), 'week');
    } catch {
        return '';
    }
}

async function cargarFeed(feed) {
    const controlador = new AbortController();
    const timeoutId = setTimeout(() => controlador.abort(), TIMEOUT_POR_FEED_MS);

    try {
        const resp = await fetch(RSS2JSON_ENDPOINT + encodeURIComponent(feed.url), { signal: controlador.signal });
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
                link: normalizarUrlHttpsOVacio(item.link),
                imagen: extraerImagen(item),
                fuente,
                categoria: feed.categoria,
                color: feed.color,
                fecha: item.pubDate ? new Date(item.pubDate).getTime() : 0
            };
        });
    } finally {
        clearTimeout(timeoutId);
    }
}

/**
 * Devuelve una lista de noticias reales de videojuegos (título, resumen corto,
 * imagen, fecha y enlace al artículo original), combinando varias fuentes,
 * ya sin duplicados de la misma historia cubierta por más de un medio.
 *
 * @param {number} maxTotal    Cuántas noticias devolver como máximo, tras combinar y filtrar.
 * @param {boolean} forzar     Si es true, ignora la caché y vuelve a consultar los feeds.
 */
export async function cargarNoticias(maxTotal = 10, forzar = false) {
    if (!forzar) {
        try {
            const cacheRaw = sessionStorage.getItem(CLAVE_CACHE);
            if (cacheRaw) {
                const cache = JSON.parse(cacheRaw);
                if (Date.now() - cache.timestamp < DURACION_CACHE_MS && Array.isArray(cache.noticias) && cache.noticias.length > 0) {
                    return { noticias: cache.noticias, actualizadoEn: cache.timestamp, deCache: true };
                }
            }
        } catch {
            // caché corrupta o no disponible: seguimos con la carga normal
        }
    }

    const resultados = await Promise.allSettled(FEEDS_NOTICIAS.map(cargarFeed));

    const candidatas = resultados
        .filter((r) => r.status === 'fulfilled')
        .flatMap((r) => r.value)
        .filter((n) => n.titulo && n.link)
        .sort((a, b) => b.fecha - a.fecha);

    // Deduplicar: si dos fuentes cubren la misma noticia, nos quedamos solo
    // con la primera que aparece (ya viene ordenada por fecha, la más reciente gana).
    const titulosVistos = new Set();
    const sinDuplicados = [];
    for (const n of candidatas) {
        const clave = normalizarTitulo(n.titulo);
        if (clave && titulosVistos.has(clave)) continue;
        if (clave) titulosVistos.add(clave);
        sinDuplicados.push(n);
    }

    // Repartir el cupo entre categorías para que ninguna se quede sin espacio
    // si, por ejemplo, "Tecnología" tuviera ese día muchas más noticias
    // recientes que "Videojuegos" (o viceversa).
    const categorias = [...new Set(sinDuplicados.map((n) => n.categoria))];
    const cupoPorCategoria = Math.ceil(maxTotal / Math.max(categorias.length, 1));
    const noticias = categorias
        .flatMap((cat) => sinDuplicados.filter((n) => n.categoria === cat).slice(0, cupoPorCategoria))
        .sort((a, b) => b.fecha - a.fecha)
        .slice(0, maxTotal);

    const actualizadoEn = Date.now();
    if (noticias.length > 0) {
        try {
            sessionStorage.setItem(CLAVE_CACHE, JSON.stringify({ timestamp: actualizadoEn, noticias }));
        } catch {
            // sessionStorage llena o bloqueada: no es crítico, simplemente no cacheamos
        }
    }

    return { noticias, actualizadoEn, deCache: false };
}
