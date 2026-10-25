// scripts/generar-noticias.mjs
// Lo ejecuta GitHub Actions cada hora (.github/workflows/noticias.yml).
// Descarga los feeds RSS de noticias, extrae titular + resumen corto + imagen
// + enlace, y guarda el resultado en noticias.json, en la raíz del sitio.
// La web lee ese archivo desde tu propio dominio: sin servicios intermedios
// (antes era rss2json.com, que en octubre 2026 empezó a bloquear con una
// verificación anti-bots) y sin problemas de CORS.
//
// Como en el agregador anterior: SOLO titular, resumen corto (máx. 140
// caracteres) y enlace al artículo original. No ampliar los resúmenes ni
// quitar el enlace/atribución.
//
// Sin dependencias externas (no hay npm install): solo Node 18+.

import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SALIDA = path.join(RAIZ, 'noticias.json');

function googleNewsRss(consulta) {
    return `https://news.google.com/rss/search?q=${encodeURIComponent(consulta)}&hl=es-419&gl=US&ceid=US:es-419`;
}

export const FEEDS = [
    { url: 'http://feeds.weblogssl.com/xataka2', categoria: 'Tecnología', fuente: 'Xataka', color: 'bg-sky-600', max: 6 },
    { url: 'https://feeds.ign.com/ign/all', categoria: 'Videojuegos', fuente: 'IGN', color: 'bg-emerald-600', max: 4 },
    { url: googleNewsRss('videojuegos'), categoria: 'Videojuegos', fuente: 'Google Noticias', color: 'bg-emerald-600', max: 4, esGoogleNews: true }
];

const MAX_RESUMEN = 140;
const MAX_TITULO = 200;
const TIMEOUT_MS = 20000;

// ---------- Utilidades de texto ----------

const ENTIDADES = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', hellip: '…', mdash: '—', ndash: '–', laquo: '«', raquo: '»', iexcl: '¡', iquest: '¿', rsquo: '’', lsquo: '‘', rdquo: '”', ldquo: '“' };
// Vocales con tilde, ñ, ü, ç (en minúscula y mayúscula): &aacute; &Ntilde; ...
for (const [letra, base] of [['a', 'a'], ['e', 'e'], ['i', 'i'], ['o', 'o'], ['u', 'u']]) {
    for (const [sufijo, marca] of [['acute', '\u0301'], ['grave', '\u0300'], ['uml', '\u0308'], ['circ', '\u0302']]) {
        ENTIDADES[letra + sufijo] = (base + marca).normalize('NFC');
        ENTIDADES[letra.toUpperCase() + sufijo] = (base.toUpperCase() + marca).normalize('NFC');
    }
}
Object.assign(ENTIDADES, { ntilde: 'ñ', Ntilde: 'Ñ', ccedil: 'ç', Ccedil: 'Ç', ordf: 'ª', ordm: 'º', euro: '€', copy: '©', reg: '®', trade: '™' });

export function decodificarEntidades(t) {
    return String(t ?? '').replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (m, e) => {
        if (e[0] === '#') {
            const n = e[1].toLowerCase() === 'x' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10);
            try { return Number.isFinite(n) && n > 0 && n <= 0x10ffff ? String.fromCodePoint(n) : ''; } catch { return ''; }
        }
        return ENTIDADES[e] ?? ENTIDADES[e.toLowerCase()] ?? m;
    });
}

const quitarCdata = (t) => String(t ?? '').replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1');

// Contenido de una etiqueta como "HTML" (CDATA quitado, entidades decodificadas)
function contenidoHtml(item, etiqueta) {
    const nombre = etiqueta.replace(/[:]/g, '\\:');
    const m = item.match(new RegExp(`<${nombre}(?:\\s[^>]*)?>([\\s\\S]*?)</${nombre}>`, 'i'));
    if (!m) return '';
    const crudo = m[1];
    // Si venía en CDATA, el contenido ya es HTML literal; si no, el HTML viene "escapado" con entidades.
    return /<!\[CDATA\[/.test(crudo) ? quitarCdata(crudo) : decodificarEntidades(crudo);
}

export function htmlATexto(html) {
    let t = String(html ?? '')
        .replace(/<(script|style)[\s\S]*?<\/\1>/gi, ' ')
        .replace(/<[^>]*>/g, ' ');
    t = decodificarEntidades(t).replace(/[<>]/g, ' ');
    return t.replace(/\s+/g, ' ').replace(/\s+([.,;:!?…)])/g, '$1').trim();
}

function recortar(texto, max) {
    return texto.length > max ? texto.slice(0, max).trim() + '…' : texto;
}

export function urlHttps(url) {
    try {
        const u = new URL(String(url ?? '').trim());
        if (u.protocol === 'http:') u.protocol = 'https:';
        return u.protocol === 'https:' ? u.href : null;
    } catch {
        return null;
    }
}

function atributo(item, etiqueta, attr) {
    const nombre = etiqueta.replace(/[:]/g, '\\:');
    const re = new RegExp(`<${nombre}\\b[^>]*\\b${attr}=["']([^"']+)["'][^>]*>`, 'gi');
    const salida = [];
    let m;
    while ((m = re.exec(item))) salida.push({ valor: decodificarEntidades(m[1]), etiqueta: m[0] });
    return salida;
}

function primeraImagenEnHtml(html) {
    const m = String(html ?? '').match(/<img[^>]+src=["']([^"']+)["']/i);
    return m ? decodificarEntidades(m[1]) : null;
}

function extraerImagen(item, descripcionHtml, contenidoEncoded) {
    const candidatas = [
        ...atributo(item, 'media:content', 'url').filter((a) => !/medium=["'](video|audio)/i.test(a.etiqueta)).map((a) => a.valor),
        ...atributo(item, 'media:thumbnail', 'url').map((a) => a.valor),
        ...atributo(item, 'enclosure', 'url').filter((a) => /type=["']image\//i.test(a.etiqueta)).map((a) => a.valor),
        primeraImagenEnHtml(contenidoEncoded),
        primeraImagenEnHtml(descripcionHtml)
    ];
    for (const c of candidatas) {
        const u = urlHttps(c);
        if (u) return u;
    }
    return null;
}

function separarFuenteDeGoogleNews(tituloCrudo) {
    const idx = tituloCrudo.lastIndexOf(' - ');
    if (idx === -1) return { titulo: tituloCrudo, fuente: 'Google Noticias' };
    return { titulo: tituloCrudo.slice(0, idx).trim(), fuente: tituloCrudo.slice(idx + 3).trim().slice(0, 60) || 'Google Noticias' };
}

// ---------- Parser de RSS 2.0 ----------

export function parsearFeed(xml, feed) {
    const items = String(xml).match(/<item\b[\s\S]*?<\/item>/gi) || [];
    const salida = [];
    for (const item of items) {
        let titulo = htmlATexto(contenidoHtml(item, 'title'));
        let fuente = feed.fuente;
        if (feed.esGoogleNews) ({ titulo, fuente } = separarFuenteDeGoogleNews(titulo));
        titulo = recortar(titulo, MAX_TITULO);

        const link = urlHttps(htmlATexto(contenidoHtml(item, 'link')));
        if (!titulo || !link) continue;

        const descripcionHtml = contenidoHtml(item, 'description');
        const contenidoEncoded = contenidoHtml(item, 'content:encoded');
        const fechaTexto = htmlATexto(contenidoHtml(item, 'pubDate'));
        const fecha = Date.parse(fechaTexto);

        salida.push({
            titulo,
            resumen: recortar(htmlATexto(descripcionHtml), MAX_RESUMEN),
            link,
            imagen: extraerImagen(item, descripcionHtml, contenidoEncoded),
            fuente,
            categoria: feed.categoria,
            color: feed.color,
            fecha: Number.isFinite(fecha) ? fecha : 0
        });
        if (salida.length >= (feed.max || 3)) break;
    }
    return salida;
}

async function descargar(feed) {
    const resp = await fetch(feed.url, {
        redirect: 'follow',
        signal: AbortSignal.timeout(TIMEOUT_MS),
        headers: {
            'User-Agent': 'KazokuGaming-Noticias/1.0 (+https://www.kazokugaming.com)',
            'Accept': 'application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.5'
        }
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return parsearFeed(await resp.text(), feed);
}

async function main() {
    const resultados = await Promise.allSettled(FEEDS.map(descargar));
    const noticias = [];
    const fuentesConError = [];
    resultados.forEach((r, i) => {
        if (r.status === 'fulfilled' && r.value.length) {
            noticias.push(...r.value);
            console.log(`✓ ${FEEDS[i].fuente}: ${r.value.length} noticias`);
        } else {
            const motivo = r.status === 'rejected' ? r.reason?.message : 'sin noticias';
            fuentesConError.push(FEEDS[i].fuente);
            console.warn(`✗ ${FEEDS[i].fuente}: ${motivo}`);
        }
    });

    if (noticias.length === 0) {
        // No sobrescribimos: la web sigue mostrando las últimas noticias buenas.
        console.warn('Ninguna fuente respondió. Se conserva el noticias.json anterior.');
        return;
    }

    noticias.sort((a, b) => b.fecha - a.fecha);

    // Solo reescribimos si cambiaron las noticias (así no se crea un commit
    // cada hora cuando no hay nada nuevo).
    try {
        const anterior = JSON.parse(await readFile(SALIDA, 'utf8'));
        if (JSON.stringify(anterior.noticias) === JSON.stringify(noticias)) {
            console.log('Sin cambios en las noticias.');
            return;
        }
    } catch {
        // no existía o estaba corrupto: lo creamos
    }

    const datos = { generado: Date.now(), fuentesConError, noticias };
    await writeFile(SALIDA, JSON.stringify(datos, null, 2) + '\n', 'utf8');
    console.log(`noticias.json actualizado con ${noticias.length} noticias.`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
    main().catch((e) => {
        console.error(e);
        process.exitCode = 1;
    });
}
