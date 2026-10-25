// pagina-juego.js
// Parte "en vivo" de las páginas de cada juego (juego-*.html): escuadrones y
// partidas reales de ese juego, leídos de Firestore. El texto de cada página
// es HTML estático (para que Google lo lea); esto solo rellena las listas.
// La página indica su juego con <body data-juego="Valorant">.

import {
    collection, query, where, limit, onSnapshot
} from "https://www.gstatic.com/firebasejs/13.1.0/firebase-firestore.js";
import { db } from './firebase-init.js';
import { skeletonCards } from './ui-utils.js';
import { juegoPorValor } from './comunidad.js';

const sanitizarHTML = (t) => String(t ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const msDe = (d) => (d?.creadoEn?.toMillis ? d.creadoEn.toMillis() : 0);

document.addEventListener('DOMContentLoaded', () => {
    const juego = juegoPorValor(document.body.dataset.juego);
    if (!juego) return;

    const contEscuadrones = document.getElementById('lista-escuadrones-juego');
    const contPartidas = document.getElementById('lista-partidas-juego');

    if (contEscuadrones) {
        contEscuadrones.innerHTML = skeletonCards(2);
        onSnapshot(query(collection(db, 'escuadrones'), where('juego', '==', juego.valor), limit(12)), (snap) => {
            const lista = snap.docs.map((d) => ({ id: d.id, ...d.data() })).sort((a, b) => msDe(b) - msDe(a)).slice(0, 6);
            if (!lista.length) {
                contEscuadrones.innerHTML = `
                    <div class="col-span-full glass-panel rounded-2xl p-6 text-center">
                        <p class="text-slate-300 font-bold mb-1">Todavía no hay escuadrones de ${sanitizarHTML(juego.nombre)}.</p>
                        <p class="text-slate-500 text-sm mb-4">Funda el primero: los que lleguen después te encontrarán aquí.</p>
                        <a href="grupos.html" class="inline-block px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl transition-colors">Fundar escuadrón</a>
                    </div>`;
                return;
            }
            contEscuadrones.innerHTML = lista.map((e) => {
                const miembros = Array.isArray(e.miembros) ? e.miembros.length : 0;
                return `
                    <a href="grupos.html?juego=${encodeURIComponent(juego.valor)}" class="glass-panel rounded-2xl p-5 block hover:border-emerald-500/50 transition-all hover:-translate-y-1">
                        <div class="flex justify-between items-start gap-3 mb-2">
                            <h3 class="font-black text-white text-lg leading-tight">${sanitizarHTML(e.nombre)}</h3>
                            <span class="text-xs font-bold text-slate-400 whitespace-nowrap">👥 ${sanitizarHTML(String(miembros))}/${sanitizarHTML(String(e.capacidad ?? '?'))}</span>
                        </div>
                        <p class="text-sm text-slate-400 line-clamp-2">${sanitizarHTML(e.descripcion || '')}</p>
                    </a>`;
            }).join('');
        }, (error) => {
            console.error('No se pudieron cargar los escuadrones:', error);
            contEscuadrones.innerHTML = `<p class="col-span-full text-slate-500 text-center py-6">No se pudieron cargar los escuadrones.</p>`;
        });
    }

    if (contPartidas) {
        contPartidas.innerHTML = skeletonCards(2);
        onSnapshot(query(collection(db, 'partidas'), where('juego', '==', juego.valor), limit(12)), (snap) => {
            const lista = snap.docs.map((d) => ({ id: d.id, ...d.data() })).sort((a, b) => msDe(b) - msDe(a)).slice(0, 6);
            if (!lista.length) {
                contPartidas.innerHTML = `
                    <div class="col-span-full glass-panel rounded-2xl p-6 text-center">
                        <p class="text-slate-300 font-bold mb-1">Nadie está buscando gente para ${sanitizarHTML(juego.nombre)} ahora mismo.</p>
                        <p class="text-slate-500 text-sm mb-4">Publica una partida y la verá toda la comunidad al instante.</p>
                        <a href="index.html#crear-partida" class="inline-block px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-colors">Invitar a jugar</a>
                    </div>`;
                return;
            }
            contPartidas.innerHTML = lista.map((p) => `
                <a href="index.html#grupos-buscando-gente" class="glass-panel rounded-2xl p-5 block hover:border-indigo-500/50 transition-all hover:-translate-y-1">
                    <h3 class="font-bold text-white mb-1">${sanitizarHTML(p.nivel)}</h3>
                    <p class="text-sm text-slate-400 line-clamp-2 mb-3">${sanitizarHTML(p.mensaje)}</p>
                    <div class="flex justify-between text-xs text-slate-500">
                        <span>por ${sanitizarHTML(p.autorNombre)}</span>
                        <span class="font-bold text-slate-300">Buscan ${sanitizarHTML(String(p.espacios))} más</span>
                    </div>
                </a>`).join('');
        }, (error) => {
            console.error('No se pudieron cargar las partidas:', error);
            contPartidas.innerHTML = `<p class="col-span-full text-slate-500 text-center py-6">No se pudieron cargar las partidas.</p>`;
        });
    }
});
