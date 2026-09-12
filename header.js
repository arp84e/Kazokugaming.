// header.js
// Módulo ES (se carga como <script type="module" src="header.js"></script>).
// Inyecta la navegación, refleja el estado real de sesión, y muestra una
// campanita 🔔 con notificaciones de mensajes nuevos en los escuadrones
// de los que el usuario es miembro.

import { auth, db, onAuthStateChanged, signOut, sendEmailVerification, serverTimestamp } from './firebase-init.js';
import {
    doc, onSnapshot, updateDoc, collection, query, where, orderBy, limit
} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js";

function getPrefix() {
    const path = window.location.pathname;
    const isRoot = path.endsWith('index.html') || path.split('/').pop() === '';
    return isRoot ? '' : '../';
}

function renderHeader(prefix) {
    return `
    <header class="border-b border-indigo-900/50 bg-[#0a0a0f]/95 backdrop-blur-xl sticky top-0 z-50 shadow-[0_4px_30px_rgba(79,70,229,0.15)]">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">

            <!-- LOGO -->
            <a href="${prefix}index.html" class="flex items-center gap-2 text-2xl font-black tracking-tighter relative z-50">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-fuchsia-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30">K</div>
                <span class="bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                    KAZOKU<span class="text-indigo-400 font-bold">GAMING</span>
                </span>
            </a>

            <!-- NAVEGACIÓN DESKTOP -->
            <nav class="hidden md:flex space-x-8 items-center bg-slate-900/50 px-6 py-2 rounded-full border border-slate-800">
                <a href="${prefix}index.html" class="text-sm font-bold text-slate-300 hover:text-indigo-400 transition flex items-center gap-2">🎯 Comunidad</a>
                <a href="${prefix}torneos.html" class="text-sm font-bold text-slate-300 hover:text-fuchsia-400 transition flex items-center gap-2">🏆 Eventos</a>
                <a href="${prefix}grupos.html" class="text-sm font-bold text-slate-300 hover:text-emerald-400 transition flex items-center gap-2">🛡️ Familias</a>
            </nav>

            <!-- PERFIL / ACCESO (se rellena según el estado de sesión) -->
            <div id="zona-sesion" class="hidden lg:flex items-center gap-4">
                <a href="${prefix}login.html" class="text-sm font-semibold text-slate-300 hover:text-white transition">Mi Perfil</a>
                <button id="btn-crear-evento" class="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-sm font-bold rounded-xl transition-all shadow-lg shadow-indigo-500/25 hover:scale-105">
                    + Invitar a Jugar
                </button>
            </div>

            <!-- MENÚ MÓVIL (BOTÓN) -->
            <div class="md:hidden flex items-center gap-1 relative z-50">
                <div id="zona-notificaciones-movil"></div>
                <button id="mobile-menu-btn" class="text-slate-300 p-2 hover:text-white transition">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
                </button>
            </div>
        </div>

        <!-- MENÚ MÓVIL (DESPLEGABLE) -->
        <div id="mobile-menu" class="hidden md:hidden bg-[#0a0a0f] border-b border-indigo-900/50 absolute w-full left-0 top-20 shadow-2xl backdrop-blur-xl">
            <nav class="flex flex-col px-6 pt-4 pb-8 space-y-4">
                <a href="${prefix}index.html" class="text-base font-bold text-slate-300">🎯 Comunidad Activa</a>
                <a href="${prefix}torneos.html" class="text-base font-bold text-slate-300">🏆 Eventos Especiales</a>
                <a href="${prefix}grupos.html" class="text-base font-bold text-slate-300">🛡️ Unirse a una Familia</a>
                <hr class="border-slate-800">
                <div id="zona-sesion-movil" class="w-full py-3 bg-indigo-600 text-center block text-white font-bold rounded-xl mt-4">
                    <a href="${prefix}login.html" class="block">Mi Perfil</a>
                </div>
            </nav>
        </div>
    </header>`;
}

function pintarSesionActiva(gamertag, prefix) {
    const zona = document.getElementById('zona-sesion');
    const zonaMovil = document.getElementById('zona-sesion-movil');
    if (zona) {
        zona.innerHTML = `
            <div id="zona-notificaciones-desktop" class="relative"></div>
            <a href="${prefix}perfil.html" class="text-sm font-bold text-emerald-400 flex items-center gap-2 hover:text-emerald-300 transition">
                <span class="w-2 h-2 rounded-full bg-emerald-500"></span> ${gamertag}
            </a>
            <button id="btn-crear-evento" class="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-sm font-bold rounded-xl transition-all shadow-lg shadow-indigo-500/25 hover:scale-105">
                + Invitar a Jugar
            </button>
            <button id="btn-cerrar-sesion" class="text-sm font-semibold text-slate-400 hover:text-red-400 transition">Salir</button>
        `;
        document.getElementById('btn-cerrar-sesion')?.addEventListener('click', () => {
            signOut(auth).then(() => window.location.href = `${prefix}index.html`);
        });
    }
    if (zonaMovil) {
        zonaMovil.innerHTML = `<a href="${prefix}perfil.html" class="text-white block">👋 ${gamertag} · Mi Perfil</a>`;
        zonaMovil.classList.remove('bg-indigo-600');
    }
}

// ============================================================
// NOTIFICACIONES: mensajes nuevos en los escuadrones del usuario
// ============================================================
// Cómo funciona: cada usuario guarda en su propio documento
// (usuarios/{uid}.ultimasLecturas.{escuadronId}) la fecha de la última vez
// que abrió el chat de ese escuadrón. Aquí comparamos esa fecha contra el
// mensaje más reciente de cada escuadrón del que el usuario es miembro.
// Evita inicializar las notificaciones más de una vez por carga de página
// (onAuthStateChanged puede disparar más de una vez en la misma sesión).
let notificacionesIniciadas = false;

function iniciarNotificaciones(uid, prefix) {
    if (notificacionesIniciadas) return;
    notificacionesIniciadas = true;

    const sanitizarHTML = (t) => { const el = document.createElement('div'); el.textContent = t ?? ''; return el.innerHTML; };

    let ultimasLecturas = {};
    let ultimasLecturasPartidas = {};
    let ultimosNoLeidos = [];
    // Map<escuadronId, { nombre, ultimoMensajeMillis, unsubscribeMensajes }>
    const escuadronesSeguidos = new Map();
    // Map<partidaId, { nombre, ultimoMensajeMillis, unsubscribeMensajes }>
    const partidasSeguidas = new Map();

    function pintarCampanita() {
        const noLeidos = [];
        escuadronesSeguidos.forEach((info, escuadronId) => {
            if (info.ultimoMensajeMillis == null) return;
            const leidoEn = ultimasLecturas[escuadronId]?.toMillis ? ultimasLecturas[escuadronId].toMillis() : 0;
            if (info.ultimoMensajeMillis > leidoEn) {
                noLeidos.push({ id: escuadronId, nombre: info.nombre, tipo: 'escuadrón' });
            }
        });
        partidasSeguidas.forEach((info, partidaId) => {
            if (info.ultimoMensajeMillis == null) return;
            const leidoEn = ultimasLecturasPartidas[partidaId]?.toMillis ? ultimasLecturasPartidas[partidaId].toMillis() : 0;
            if (info.ultimoMensajeMillis > leidoEn) {
                noLeidos.push({ id: partidaId, nombre: info.nombre, tipo: 'partida' });
            }
        });
        ultimosNoLeidos = noLeidos;

        const hayNoLeidos = noLeidos.length > 0;
        const badge = hayNoLeidos
            ? `<span class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[10px] font-black rounded-full flex items-center justify-center border-2 border-[#0a0a0f]">${noLeidos.length > 9 ? '9+' : noLeidos.length}</span>`
            : '';

        const htmlBoton = `
            <button id="btn-notificaciones" class="relative text-slate-300 hover:text-white transition p-2" aria-label="Notificaciones">
                <span class="text-xl">🔔</span>
                ${badge}
            </button>
            <div id="panel-notificaciones" class="hidden absolute right-0 top-12 w-72 bg-[#0a0a0f] border border-slate-800 rounded-xl shadow-2xl overflow-hidden z-50">
                <div class="p-3 border-b border-slate-800 text-sm font-bold text-white">Notificaciones</div>
                <div class="max-h-72 overflow-y-auto">
                    ${hayNoLeidos
                        ? noLeidos.map(n => `
                            <a href="${prefix}${n.tipo === 'escuadrón' ? 'grupos.html' : 'index.html'}" class="block px-4 py-3 hover:bg-slate-900 border-b border-slate-800/50 text-sm">
                                <span class="text-emerald-400 font-bold">●</span>
                                <span class="text-slate-200">Mensajes nuevos en ${n.tipo === 'escuadrón' ? 'el escuadrón' : 'la partida'} <strong class="text-white">${sanitizarHTML(n.nombre)}</strong></span>
                            </a>`).join('')
                        : `<p class="px-4 py-6 text-center text-slate-500 text-sm">No hay mensajes nuevos.</p>`}
                </div>
            </div>`;

        const zonaDesktop = document.getElementById('zona-notificaciones-desktop');
        const zonaMovil = document.getElementById('zona-notificaciones-movil');
        if (zonaDesktop) zonaDesktop.innerHTML = htmlBoton;
        if (zonaMovil) zonaMovil.innerHTML = `
            <button id="btn-notificaciones-movil" class="relative text-slate-300 hover:text-white transition p-2" aria-label="Notificaciones">
                <span class="text-xl">🔔</span>
                ${hayNoLeidos ? '<span class="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border border-[#0a0a0f]"></span>' : ''}
            </button>`;

        // Reabrir/cerrar el desplegable (delegado a nivel de documento, ver abajo)
    }

    // Desplegable: clic en la campanita lo abre/cierra; clic fuera lo cierra.
    document.addEventListener('click', (e) => {
        const panel = document.getElementById('panel-notificaciones');
        if (!panel) return;
        if (e.target.closest('#btn-notificaciones')) {
            panel.classList.toggle('hidden');
        } else if (!e.target.closest('#panel-notificaciones')) {
            panel.classList.add('hidden');
        }
        if (e.target.closest('#btn-notificaciones-movil')) {
            const primero = ultimosNoLeidos[0];
            window.location.href = `${prefix}${primero && primero.tipo === 'partida' ? 'index.html' : 'grupos.html'}`;
        }
    });

    // 1. Escuchar el perfil del usuario para saber qué ha leído
    onSnapshot(doc(db, 'usuarios', uid), (snap) => {
        const datos = snap.exists() ? snap.data() : {};
        ultimasLecturas = datos.ultimasLecturas || {};
        ultimasLecturasPartidas = datos.ultimasLecturasPartidas || {};
        pintarCampanita();
    });

    // 2. Escuchar de qué escuadrones es miembro, y para cada uno, su último mensaje
    const qMisEscuadrones = query(collection(db, 'escuadrones'), where('miembros', 'array-contains', uid));
    onSnapshot(qMisEscuadrones, (snap) => {
        const idsActuales = new Set(snap.docs.map(d => d.id));

        // Dejar de escuchar escuadrones de los que ya no somos miembros
        escuadronesSeguidos.forEach((info, id) => {
            if (!idsActuales.has(id)) {
                info.unsubscribeMensajes?.();
                escuadronesSeguidos.delete(id);
            }
        });

        // Empezar a escuchar los escuadrones nuevos
        snap.docs.forEach((d) => {
            if (escuadronesSeguidos.has(d.id)) return;
            const nombre = d.data().nombre || 'Escuadrón';
            const info = { nombre, ultimoMensajeMillis: null, unsubscribeMensajes: null };
            escuadronesSeguidos.set(d.id, info);

            const qUltimoMsg = query(collection(db, 'escuadrones', d.id, 'mensajes'), orderBy('creadoEn', 'desc'), limit(1));
            info.unsubscribeMensajes = onSnapshot(qUltimoMsg, (msgSnap) => {
                if (!msgSnap.empty) {
                    const ts = msgSnap.docs[0].data().creadoEn;
                    info.ultimoMensajeMillis = ts?.toMillis ? ts.toMillis() : Date.now();
                }
                pintarCampanita();
            });
        });

        pintarCampanita();
    });

    // 3. Escuchar mis partidas (como autor o como interesado), y su último mensaje.
    // Se usan dos consultas por separado (en vez de un OR) para no depender de
    // índices compuestos especiales en Firestore.
    let idsPartidasAutor = new Set();
    let idsPartidasInteresado = new Set();
    const datosPartidasCache = new Map();

    function recalcularPartidasSeguidas() {
        const idsActuales = new Set([...idsPartidasAutor, ...idsPartidasInteresado]);

        partidasSeguidas.forEach((info, id) => {
            if (!idsActuales.has(id)) {
                info.unsubscribeMensajes?.();
                partidasSeguidas.delete(id);
            }
        });

        idsActuales.forEach((id) => {
            if (partidasSeguidas.has(id)) return;
            const data = datosPartidasCache.get(id) || {};
            const info = { nombre: data.nivel || 'Partida', ultimoMensajeMillis: null, unsubscribeMensajes: null };
            partidasSeguidas.set(id, info);

            const qUltimoMsg = query(collection(db, 'partidas', id, 'mensajes'), orderBy('creadoEn', 'desc'), limit(1));
            info.unsubscribeMensajes = onSnapshot(qUltimoMsg, (msgSnap) => {
                if (!msgSnap.empty) {
                    const ts = msgSnap.docs[0].data().creadoEn;
                    info.ultimoMensajeMillis = ts?.toMillis ? ts.toMillis() : Date.now();
                }
                pintarCampanita();
            });
        });

        pintarCampanita();
    }

    const qMisPartidasAutor = query(collection(db, 'partidas'), where('autorId', '==', uid));
    onSnapshot(qMisPartidasAutor, (snap) => {
        idsPartidasAutor = new Set(snap.docs.map(d => d.id));
        snap.docs.forEach(d => datosPartidasCache.set(d.id, d.data()));
        recalcularPartidasSeguidas();
    });

    const qMisPartidasInteresado = query(collection(db, 'partidas'), where('interesados', 'array-contains', uid));
    onSnapshot(qMisPartidasInteresado, (snap) => {
        idsPartidasInteresado = new Set(snap.docs.map(d => d.id));
        snap.docs.forEach(d => datosPartidasCache.set(d.id, d.data()));
        recalcularPartidasSeguidas();
    });
}

// ============================================================
// AVISO DE CORREO SIN VERIFICAR
// ============================================================
function mostrarBannerVerificacion(user) {
    if (document.getElementById('banner-verificacion-correo')) return; // ya está mostrado

    const container = document.getElementById('header-container');
    if (!container) return;

    const banner = document.createElement('div');
    banner.id = 'banner-verificacion-correo';
    banner.className = 'bg-amber-500/10 border-b border-amber-500/30 text-amber-300 text-xs sm:text-sm text-center py-2 px-4 sticky top-20 z-40';
    banner.innerHTML = `
        ⚠️ Verifica tu correo (<strong>${user.email}</strong>) para asegurar tu cuenta.
        <button id="btn-reenviar-verificacion" class="underline hover:text-amber-100 font-bold ml-2">Reenviar correo</button>
    `;
    container.insertAdjacentElement('afterend', banner);

    document.getElementById('btn-reenviar-verificacion').addEventListener('click', async () => {
        const btn = document.getElementById('btn-reenviar-verificacion');
        try {
            await sendEmailVerification(user);
            btn.innerText = 'Enviado ✓';
            btn.disabled = true;
        } catch (error) {
            console.error("No se pudo reenviar el correo de verificación:", error);
            alert('No se pudo reenviar el correo. Espera un momento e inténtalo de nuevo.');
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const prefix = getPrefix();
    const container = document.getElementById('header-container');
    if (!container) return;

    container.innerHTML = renderHeader(prefix);

    document.getElementById('mobile-menu-btn')?.addEventListener('click', () => {
        document.getElementById('mobile-menu').classList.toggle('hidden');
    });

    // El botón "+ Invitar a Jugar" solo tiene su acción propia dentro de index.html.
    // Si se pulsa desde cualquier otra página, llevamos a la persona a index.html
    // y le indicamos (vía hash) que abra el modal de crear partida al llegar.
    const enIndex = window.location.pathname.endsWith('index.html') || window.location.pathname.split('/').pop() === '';
    document.addEventListener('click', (e) => {
        if (e.target.closest('#btn-crear-evento') && !enIndex) {
            window.location.href = `${prefix}index.html#crear-partida`;
        }
    });

    // Refleja el estado real de autenticación en cuanto Firebase lo confirme
    onAuthStateChanged(auth, (user) => {
        if (user) {
            const gamertag = user.displayName || user.email.split('@')[0];
            pintarSesionActiva(gamertag, prefix);
            iniciarNotificaciones(user.uid, prefix);
            if (!user.emailVerified) mostrarBannerVerificacion(user);
        }
        // Si no hay usuario, se deja el estado por defecto ("Mi Perfil") ya renderizado.
    });
});
