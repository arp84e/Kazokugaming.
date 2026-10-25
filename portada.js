// portada.js
// Secciones "vivas" de la portada (index.html): tarjetas de juegos,
// contadores con mínimo, agenda semanal, próximo torneo, lo último del Muro
// (y la publicación más 🔥 de la semana), streamers y Discord.
// Lo que se muestra se configura en comunidad.js.

import {
    collection, query, orderBy, limit, getDocs, getCountFromServer
} from "https://www.gstatic.com/firebasejs/13.1.0/firebase-firestore.js";
import { db } from './firebase-init.js';
import { formatearTiempoRelativo } from './noticias.js';
import {
    JUEGOS, juegoPorValor, AGENDA_SEMANAL, ZONA_HORARIA_AGENDA, proximaOcurrencia,
    STREAMERS, enlaceTwitch, enlaceDiscord, UMBRALES_ESTADISTICAS
} from './comunidad.js';

const sanitizarHTML = (t) => String(t ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const $ = (id) => document.getElementById(id);

const GRADIENTES_AVATAR = ['from-indigo-500 to-fuchsia-500', 'from-cyan-500 to-blue-600', 'from-emerald-500 to-teal-600', 'from-amber-500 to-orange-600', 'from-rose-500 to-pink-600', 'from-violet-500 to-purple-600'];
function gradienteDe(nombre) {
    let h = 0;
    for (const c of String(nombre || '')) h = (h * 31 + c.codePointAt(0)) >>> 0;
    return GRADIENTES_AVATAR[h % GRADIENTES_AVATAR.length];
}
const inicialesDe = (n) => (String(n || '??').trim().split(/\s+/).slice(0, 2).map((p) => p[0]?.toUpperCase() || '').join('') || '??');

// ---------- 1. Tarjetas "Elige tu juego" ----------
function pintarJuegos() {
    const rejilla = $('rejilla-juegos');
    if (!rejilla) return;
    rejilla.innerHTML = JUEGOS.map((j) => `
        <a href="juego-${sanitizarHTML(j.slug)}.html" class="group relative rounded-2xl overflow-hidden border border-slate-800 hover:border-white/30 transition-all hover:-translate-y-1 aspect-[4/5] flex flex-col justify-end p-4 bg-gradient-to-br ${j.degradado}">
            <span class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent"></span>
            <span class="absolute top-3 left-3 text-white/90 font-black font-display text-2xl tracking-tight drop-shadow" aria-hidden="true">${sanitizarHTML(j.sigla)}</span>
            <span class="absolute -right-4 -top-4 w-24 h-24 rounded-full bg-white/10 group-hover:scale-125 transition-transform duration-500" aria-hidden="true"></span>
            <span class="relative font-black text-white leading-tight">${sanitizarHTML(j.nombre)}</span>
            <span class="relative text-[11px] text-white/70 font-semibold">${sanitizarHTML(j.genero)}</span>
        </a>`).join('');
}

// ---------- 2. Contadores: solo los que superan su mínimo ----------
async function pintarEstadisticas() {
    const seccion = $('seccion-estadisticas');
    if (!seccion) return;
    let conteos;
    try {
        const [esc, tor, usr] = await Promise.all([
            getCountFromServer(collection(db, 'escuadrones')),
            getCountFromServer(collection(db, 'torneos')),
            getCountFromServer(collection(db, 'usuarios'))
        ]);
        conteos = { escuadrones: esc.data().count, torneos: tor.data().count, jugadores: usr.data().count };
    } catch (error) {
        console.error('No se pudieron cargar las estadísticas:', error);
        return;
    }
    const visibles = Object.keys(conteos).filter((k) => conteos[k] >= (UMBRALES_ESTADISTICAS[k] ?? Infinity));
    if (!visibles.length) return; // aún pocos: mejor no mostrar nada que mostrar "3 jugadores"

    visibles.forEach((k) => seccion.querySelector(`[data-stat="${k}"]`)?.classList.remove('hidden'));
    const rejilla = $('rejilla-estadisticas');
    rejilla.classList.remove('grid-cols-3');
    rejilla.classList.add(['grid-cols-1', 'grid-cols-2', 'grid-cols-3'][visibles.length - 1]);
    seccion.classList.remove('hidden');

    const animar = (el, destino) => {
        const inicio = performance.now();
        const frame = (ahora) => {
            const t = Math.min((ahora - inicio) / 1200, 1);
            el.textContent = Math.floor(t * destino).toLocaleString('es-ES');
            if (t < 1) requestAnimationFrame(frame);
        };
        requestAnimationFrame(frame);
    };
    const arrancar = () => visibles.forEach((k) => animar($(`stat-${k}`), conteos[k]));
    if ('IntersectionObserver' in window) {
        const obs = new IntersectionObserver((entradas) => {
            if (entradas.some((e) => e.isIntersecting)) { obs.disconnect(); arrancar(); }
        }, { threshold: 0.3 });
        obs.observe(seccion);
    } else {
        arrancar();
    }
}

// ---------- 3. Lo que viene: agenda semanal + próximo torneo ----------
const fmtDiaHora = (fecha) => fecha.toLocaleString('es-ES', { timeZone: ZONA_HORARIA_AGENDA, weekday: 'long', hour: '2-digit', minute: '2-digit' });

function cuentaRegresiva(ms) {
    const diff = ms - Date.now();
    if (diff <= 0) return '¡Ahora!';
    const d = Math.floor(diff / 86400000), h = Math.floor((diff % 86400000) / 3600000), m = Math.floor((diff % 3600000) / 60000);
    return d > 0 ? `en ${d}d ${h}h` : h > 0 ? `en ${h}h ${m}m` : `en ${m} min`;
}

function pintarAgenda() {
    const bloque = $('bloque-agenda');
    const eventos = AGENDA_SEMANAL
        .map((ev) => ({ ev, juego: juegoPorValor(ev.juego), cuando: proximaOcurrencia(ev) }))
        .filter((x) => x.cuando)
        .sort((a, b) => a.cuando - b.cuando);
    if (!bloque || !eventos.length) return false;
    bloque.innerHTML = eventos.map(({ ev, juego, cuando }) => `
        <div class="glass-panel rounded-2xl p-5 flex gap-4 items-start">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br ${juego ? juego.degradado : 'from-indigo-500 to-fuchsia-500'} flex items-center justify-center text-white font-black text-sm shrink-0 font-display">${sanitizarHTML(juego ? juego.sigla : '🎮')}</div>
            <div class="min-w-0">
                <p class="text-xs font-bold uppercase tracking-wider text-indigo-300">Cada ${sanitizarHTML(fmtDiaHora(cuando))} h</p>
                <h3 class="font-black text-white text-lg leading-tight">${sanitizarHTML(ev.titulo || ev.juego)}</h3>
                ${ev.descripcion ? `<p class="text-sm text-slate-400 mt-1">${sanitizarHTML(ev.descripcion)}</p>` : ''}
                <p class="text-xs font-bold text-emerald-400 mt-2" data-cuenta="${cuando.getTime()}">Próxima: ${sanitizarHTML(cuentaRegresiva(cuando.getTime()))}</p>
                ${juego ? `<a href="juego-${sanitizarHTML(juego.slug)}.html" class="inline-block mt-2 text-xs font-bold text-slate-300 hover:text-white underline">Ver grupos de ${sanitizarHTML(juego.nombre)}</a>` : ''}
            </div>
        </div>`).join('');
    bloque.classList.remove('hidden');
    return true;
}

async function pintarProximoTorneo() {
    const bloque = $('bloque-proximo-torneo');
    if (!bloque) return false;
    let proximo = null;
    try {
        const snap = await getDocs(query(collection(db, 'torneos'), orderBy('creadoEn', 'desc'), limit(50)));
        const ahora = Date.now();
        proximo = snap.docs
            .map((d) => ({ id: d.id, ...d.data() }))
            .filter((t) => typeof t.fecha?.toDate === 'function' && t.fecha.toDate().getTime() > ahora)
            .sort((a, b) => a.fecha.toDate() - b.fecha.toDate())[0] || null;
    } catch (error) {
        console.error('No se pudo cargar el próximo torneo:', error);
    }
    if (!proximo) return false;
    const ms = proximo.fecha.toDate().getTime();
    bloque.innerHTML = `
        <a href="torneos.html" class="block h-full rounded-2xl p-6 bg-gradient-to-br from-fuchsia-600/30 via-slate-900 to-slate-950 border border-fuchsia-500/40 hover:border-fuchsia-400 transition-colors">
            <p class="text-xs font-bold uppercase tracking-wider text-fuchsia-300 mb-2">🏆 Próximo torneo</p>
            <h3 class="text-2xl font-black text-white leading-tight mb-1">${sanitizarHTML(proximo.titulo)}</h3>
            <p class="text-sm text-slate-400 mb-4">${sanitizarHTML(proximo.juego)}${proximo.formato ? ` · ${sanitizarHTML(proximo.formato)}` : ''}</p>
            <p class="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-fuchsia-400 to-amber-400" data-cuenta="${ms}">${sanitizarHTML(cuentaRegresiva(ms))}</p>
            <p class="text-xs text-slate-500 mt-1">${sanitizarHTML(new Date(ms).toLocaleString('es-ES', { dateStyle: 'full', timeStyle: 'short' }))}</p>
            ${proximo.recompensa ? `<p class="text-sm font-bold text-amber-300 mt-4">Premio: ${sanitizarHTML(proximo.recompensa)}</p>` : ''}
            <span class="inline-block mt-5 px-5 py-2.5 bg-fuchsia-600 text-white font-bold rounded-xl">Inscribirme</span>
        </a>`;
    bloque.classList.remove('hidden');
    return true;
}

async function pintarLoQueViene() {
    const hayAgenda = pintarAgenda();
    const hayTorneo = await pintarProximoTorneo();
    if (!hayAgenda && !hayTorneo) return;
    // Si solo hay uno de los dos, que ocupe todo el ancho
    if (!hayTorneo) $('bloque-agenda').classList.replace('lg:col-span-2', 'lg:col-span-3');
    if (!hayAgenda) $('bloque-proximo-torneo').classList.add('lg:col-span-3');
    $('seccion-lo-que-viene').classList.remove('hidden');
    setInterval(() => {
        document.querySelectorAll('[data-cuenta]').forEach((el) => {
            const ms = Number(el.dataset.cuenta);
            el.textContent = (el.textContent.startsWith('Próxima') ? 'Próxima: ' : '') + cuentaRegresiva(ms);
        });
    }, 30000);
}

// ---------- 4. En el Muro ----------
const msDe = (d) => (d?.creadoEn?.toMillis ? d.creadoEn.toMillis() : 0);

function tarjetaPost(p, { grande = false } = {}) {
    const likes = Array.isArray(p.likes) ? p.likes.length : 0;
    const nombre = p.autorNombre || 'Jugador';
    return `
        <a href="muro.html" class="glass-panel rounded-2xl p-5 block hover:border-cyan-500/40 transition-colors ${grande ? 'sm:p-7' : ''}">
            <div class="flex items-center gap-3 mb-3">
                <span class="w-10 h-10 rounded-xl bg-gradient-to-br ${gradienteDe(nombre)} flex items-center justify-center text-white font-black text-sm shrink-0">${sanitizarHTML(inicialesDe(nombre))}</span>
                <div class="min-w-0">
                    <p class="font-bold text-white truncate">${sanitizarHTML(nombre)}</p>
                    <p class="text-xs text-slate-500">${sanitizarHTML(formatearTiempoRelativo(msDe(p)))}${p.juego ? ` · ${sanitizarHTML(p.juego)}` : ''}</p>
                </div>
                <span class="ml-auto text-sm font-bold ${likes ? 'text-orange-400' : 'text-slate-600'} whitespace-nowrap">🔥 ${likes}</span>
            </div>
            <p class="text-slate-200 ${grande ? 'text-lg sm:text-xl' : 'text-sm line-clamp-4'} leading-relaxed break-words">${sanitizarHTML(p.texto)}</p>
        </a>`;
}

async function pintarMuro() {
    const cont = $('ultimos-posts');
    if (!cont) return;
    let posts = [];
    try {
        const snap = await getDocs(query(collection(db, 'muro'), orderBy('creadoEn', 'desc'), limit(40)));
        posts = snap.docs.map((d) => ({ id: d.id, ...d.data() }));
    } catch (error) {
        console.error('No se pudo cargar el muro:', error);
    }

    if (!posts.length) {
        cont.innerHTML = `
            <div class="col-span-full glass-panel rounded-2xl p-8 text-center">
                <p class="text-white font-bold mb-1">El Muro está esperando la primera publicación.</p>
                <p class="text-slate-400 text-sm mb-4">Cuenta qué estás jugando, comparte un logro o busca gente para esta noche.</p>
                <a href="muro.html" class="inline-block px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-xl transition-colors">Escribir en el Muro</a>
            </div>`;
        return;
    }

    // La más 🔥 de los últimos 7 días (con al menos 3 reacciones, para que sea un reconocimiento de verdad)
    const haceUnaSemana = Date.now() - 7 * 86400000;
    const destacado = posts
        .filter((p) => msDe(p) >= haceUnaSemana && Array.isArray(p.likes) && p.likes.length >= 3)
        .sort((a, b) => b.likes.length - a.likes.length || msDe(b) - msDe(a))[0];
    if (destacado) {
        const bloque = $('destacado-semana');
        bloque.innerHTML = `
            <p class="text-xs font-bold uppercase tracking-wider text-orange-300 mb-3">🔥 Lo más encendido de la semana</p>
            ${tarjetaPost(destacado, { grande: true })}`;
        bloque.classList.remove('hidden');
    }

    cont.innerHTML = posts.filter((p) => p !== destacado).slice(0, 3).map((p) => tarjetaPost(p)).join('')
        || '<p class="col-span-full text-slate-500 text-center">Pronto habrá más publicaciones.</p>';
}

// ---------- 5. Streamers y Discord ----------
function pintarStreamers() {
    const lista = STREAMERS
        .map((s) => ({ ...s, url: enlaceTwitch(s.canal), juego: juegoPorValor(s.juego) }))
        .filter((s) => s.url);
    if (!lista.length) return;
    $('lista-streamers').innerHTML = lista.map((s) => `
        <a href="${sanitizarHTML(s.url)}" target="_blank" rel="noopener noreferrer" class="glass-panel rounded-2xl p-5 flex items-center gap-4 hover:border-[#9146FF]/60 transition-colors">
            <span class="w-12 h-12 rounded-xl bg-[#9146FF] flex items-center justify-center text-white font-black shrink-0">${sanitizarHTML(inicialesDe(s.nombre || s.canal))}</span>
            <span class="min-w-0">
                <span class="block font-bold text-white truncate">${sanitizarHTML(s.nombre || s.canal)}</span>
                <span class="block text-xs text-slate-400">${s.juego ? sanitizarHTML(s.juego.nombre) + ' · ' : ''}twitch.tv/${sanitizarHTML(String(s.canal).toLowerCase())}</span>
            </span>
        </a>`).join('');
    $('seccion-streamers').classList.remove('hidden');
}

function pintarDiscord() {
    const url = enlaceDiscord();
    if (!url) return;
    for (const id of ['btn-discord-portada', 'btn-discord-footer']) {
        const a = $(id);
        if (a) { a.href = url; a.classList.remove('hidden'); }
    }
    $('seccion-discord')?.classList.remove('hidden');
}

document.addEventListener('DOMContentLoaded', () => {
    pintarJuegos();
    pintarDiscord();
    pintarStreamers();
    pintarEstadisticas();
    pintarLoQueViene();
    pintarMuro();
});

// Para el estado vacío de "Grupos buscando gente" en index.html
export function hayAgendaSemanal() {
    return AGENDA_SEMANAL.some((ev) => proximaOcurrencia(ev));
}
