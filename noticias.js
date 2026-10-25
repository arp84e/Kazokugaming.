// noticias.js
// Muestra noticias REALES de videojuegos y tecnología como titular + imagen +
// resumen corto + enlace al artículo original. Nunca reproduce el artículo
// completo: es el mismo patrón que usa cualquier agregador de noticias
// (Google News, Feedly, Apple News...) y por diseño evita problemas de
// derechos de autor, siempre que se mantenga así — no ampliar los resúmenes
// ni quitar el enlace/atribución.
//
// DE DÓNDE SALEN (desde octubre 2026):
// Ya NO se usa rss2json.com: empezó a exigir una verificación anti-bots que
// una web no puede pasar, y las noticias dejaron de cargar. Ahora un proceso
// automático de GitHub (.github/workflows/noticias.yml +
// scripts/generar-noticias.mjs) descarga cada hora los feeds de Xataka, IGN y
// Google Noticias y guarda el resultado en noticias.json, junto a esta web.
// Esta página solo lee ese archivo desde tu propio dominio: sin servicios de
// terceros en el navegador, sin CORS y sin nada externo que pueda inyectar
// contenido. Las fuentes se cambian en scripts/generar-noticias.mjs.

const URL_NOTICIAS = 'noticias.json';
const CLAVE_CACHE = 'kazoku_noticias_cache_v7';
const DURACION_CACHE_MS = 10 * 60 * 1000; // 10 minutos
const TIMEOUT_MS = 8000;

// Aunque noticias.json lo generamos nosotros, su contenido viene de feeds de
// terceros: se vuelve a validar todo aquí (defensa en profundidad).

// Valida que una URL sea https:// y devuelve su forma NORMALIZADA (url.href),
// nunca la cadena original: al normalizar, caracteres como comillas quedan
// porcentaje-codificados y nunca llegan tal cual al HTML.
function normalizarUrlHttpsOVacio(url) {
    try {
        const u = new URL(url);
        return u.protocol === 'https:' ? u.href : null;
    } catch {
        return null;
    }
}

// Texto plano y acotado. Se usa DOMParser y NO un <div> con innerHTML: el
// navegador sí ejecuta los onerror/onload de un <div> suelto; DOMParser crea
// un documento "inerte" que no carga ni ejecuta nada.
function textoPlano(valor, maxLen) {
    let texto = '';
    try {
        const documento = new DOMParser().parseFromString(String(valor ?? ''), 'text/html');
        texto = documento.body ? documento.body.textContent || '' : '';
    } catch {
        texto = '';
    }
    texto = texto.replace(/\s+/g, ' ').trim();
    if (texto.length > maxLen) texto = texto.slice(0, maxLen).trim() + '…';
    return texto;
}

// Solo estas categorías/colores existen en la web: cualquier otro valor se descarta.
const CATEGORIAS = { 'Videojuegos': 'bg-emerald-600', 'Tecnología': 'bg-sky-600' };

function validarNoticia(n) {
    if (!n || typeof n !== 'object') return null;
    const categoria = Object.prototype.hasOwnProperty.call(CATEGORIAS, n.categoria) ? n.categoria : null;
    const titulo = textoPlano(n.titulo, 200);
    const link = normalizarUrlHttpsOVacio(n.link);
    if (!categoria || !titulo || !link) return null;
    const fecha = Number(n.fecha);
    return {
        titulo,
        resumen: textoPlano(n.resumen, 141),
        link,
        imagen: n.imagen ? normalizarUrlHttpsOVacio(n.imagen) : null,
        fuente: textoPlano(n.fuente, 60) || 'Noticias',
        categoria,
        color: CATEGORIAS[categoria],
        fecha: Number.isFinite(fecha) && fecha > 0 ? fecha : 0
    };
}

// Normaliza un título para poder comparar si dos noticias de fuentes
// distintas son "la misma historia" (mismo suceso cubierto por dos medios).
function normalizarTitulo(titulo) {
    return titulo
        .toLowerCase()
        .normalize('NFD').replace(/[̀-ͯ]/g, '') // quita acentos
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

async function leerArchivoNoticias() {
    const controlador = new AbortController();
    const timeoutId = setTimeout(() => controlador.abort(), TIMEOUT_MS);
    try {
        // "no-cache": revalida con el servidor para traer siempre la última versión publicada
        const resp = await fetch(URL_NOTICIAS, { cache: 'no-cache', signal: controlador.signal });
        if (!resp.ok) throw new Error(`noticias.json respondió ${resp.status}`);
        const datos = await resp.json();
        const lista = Array.isArray(datos?.noticias) ? datos.noticias : [];
        return {
            noticias: lista.slice(0, 100).map(validarNoticia).filter(Boolean),
            generado: Number(datos?.generado) || 0
        };
    } finally {
        clearTimeout(timeoutId);
    }
}

/**
 * Devuelve una lista de noticias reales de videojuegos y tecnología (título,
 * resumen corto, imagen, fecha y enlace al artículo original), ya sin
 * duplicados de la misma historia cubierta por más de un medio.
 *
 * @param {number} maxTotal    Cuántas noticias devolver como máximo.
 * @param {boolean} forzar     Si es true, ignora la caché y vuelve a pedir el archivo.
 */
export async function cargarNoticias(maxTotal = 10, forzar = false) {
    if (!forzar) {
        try {
            const cacheRaw = sessionStorage.getItem(CLAVE_CACHE);
            if (cacheRaw) {
                const cache = JSON.parse(cacheRaw);
                if (Date.now() - cache.timestamp < DURACION_CACHE_MS && Array.isArray(cache.noticias) && cache.noticias.length > 0) {
                    const noticias = cache.noticias.map(validarNoticia).filter(Boolean);
                    if (noticias.length > 0) return { noticias, actualizadoEn: cache.actualizadoEn || cache.timestamp, deCache: true };
                }
            }
        } catch {
            // caché corrupta o no disponible: seguimos con la carga normal
        }
    }

    const { noticias: candidatas, generado } = await leerArchivoNoticias();
    candidatas.sort((a, b) => b.fecha - a.fecha);

    // Deduplicar: si dos fuentes cubren la misma noticia, nos quedamos solo
    // con la más reciente.
    const titulosVistos = new Set();
    const sinDuplicados = [];
    for (const n of candidatas) {
        const clave = normalizarTitulo(n.titulo);
        if (clave && titulosVistos.has(clave)) continue;
        if (clave) titulosVistos.add(clave);
        sinDuplicados.push(n);
    }

    // Repartir el cupo entre categorías para que ninguna se quede sin espacio.
    const categorias = [...new Set(sinDuplicados.map((n) => n.categoria))];
    const cupoPorCategoria = Math.ceil(maxTotal / Math.max(categorias.length, 1));
    const noticias = categorias
        .flatMap((cat) => sinDuplicados.filter((n) => n.categoria === cat).slice(0, cupoPorCategoria))
        .sort((a, b) => b.fecha - a.fecha)
        .slice(0, maxTotal);

    // "Actualizado hace X" refleja cuándo se generó realmente el archivo
    const actualizadoEn = generado || Date.now();
    if (noticias.length > 0) {
        try {
            sessionStorage.setItem(CLAVE_CACHE, JSON.stringify({ timestamp: Date.now(), actualizadoEn, noticias }));
        } catch {
            // sessionStorage llena o bloqueada: no es crítico, simplemente no cacheamos
        }
    }

    return { noticias, actualizadoEn, deCache: false };
}
