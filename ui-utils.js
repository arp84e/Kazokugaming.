// ui-utils.js
// Utilidades de interfaz compartidas por todas las páginas:
//   - showToast(mensaje, tipo)         -> notificación flotante (reemplaza alert())
//   - showConfirm(mensaje, opciones)   -> modal de confirmación (reemplaza confirm())
//   - skeletonCards(n)                 -> HTML de tarjetas "esqueleto" mientras carga contenido
//   - skeletonRows(n)                  -> HTML de filas "esqueleto" para listas
//
// Uso:
//   import { showToast, showConfirm, skeletonCards, skeletonRows } from './ui-utils.js';
//   showToast('No se pudo enviar el mensaje.', 'error');
//   if (await showConfirm('¿Eliminar este torneo?', { danger: true })) { ... }

// Escapa & < > " ' — usado internamente para que cualquier texto dinámico
// (p. ej. el nombre de un escuadrón o el gamertag de otro usuario) que se
// pase como "titulo" a showConfirm/showReportPrompt no pueda inyectar HTML.
function escaparHTML(t) {
    return String(t ?? '').replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function asegurarContenedorToasts() {
    let cont = document.getElementById('toast-contenedor');
    if (!cont) {
        cont = document.createElement('div');
        cont.id = 'toast-contenedor';
        cont.setAttribute('aria-live', 'polite');
        cont.setAttribute('role', 'status');
        cont.className = 'fixed bottom-4 right-4 left-4 sm:left-auto z-[300] flex flex-col gap-2 items-end pointer-events-none';
        document.body.appendChild(cont);
    }
    return cont;
}

const ESTILOS_TOAST = {
    exito: 'bg-emerald-600 border-emerald-400/40',
    error: 'bg-red-600 border-red-400/40',
    info: 'bg-slate-800 border-slate-600'
};

const ICONOS_TOAST = { exito: '✓', error: '✕', info: 'ℹ' };

/**
 * Muestra una notificación flotante que desaparece sola.
 * @param {string} mensaje
 * @param {'exito'|'error'|'info'} tipo
 * @param {number} duracionMs
 */
export function showToast(mensaje, tipo = 'info', duracionMs = 4500) {
    const cont = asegurarContenedorToasts();
    const toast = document.createElement('div');
    const estilo = ESTILOS_TOAST[tipo] || ESTILOS_TOAST.info;

    toast.className = `pointer-events-auto max-w-sm w-full sm:w-auto text-white text-sm font-semibold px-4 py-3 rounded-xl border shadow-2xl flex items-start gap-2 opacity-0 translate-y-2 transition-all duration-300 ${estilo}`;
    toast.innerHTML = `<span class="shrink-0">${ICONOS_TOAST[tipo] || ICONOS_TOAST.info}</span><span>${escaparHTML(mensaje)}</span>`;
    cont.appendChild(toast);

    // Forzar reflow para que la transición de entrada se anime
    requestAnimationFrame(() => {
        toast.classList.remove('opacity-0', 'translate-y-2');
    });

    const quitar = () => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    };
    toast.addEventListener('click', quitar);
    setTimeout(quitar, duracionMs);
}

/**
 * Muestra un modal de confirmación y devuelve una Promesa<boolean>.
 * @param {string} mensaje
 * @param {{titulo?: string, confirmarTexto?: string, cancelarTexto?: string, danger?: boolean}} opciones
 */
export function showConfirm(mensaje, opciones = {}) {
    const {
        titulo = '¿Estás seguro?',
        confirmarTexto = 'Confirmar',
        cancelarTexto = 'Cancelar',
        danger = false
    } = opciones;

    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'fixed inset-0 z-[250] flex items-center justify-center p-4';
        overlay.innerHTML = `
            <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
            <div class="relative w-full max-w-sm bg-[#0a0a0f] border ${danger ? 'border-red-500/40' : 'border-slate-700'} rounded-2xl shadow-2xl p-6">
                <h3 class="text-lg font-black text-white mb-2">${escaparHTML(titulo)}</h3>
                <p class="text-sm text-slate-400 mb-6">${escaparHTML(mensaje)}</p>
                <div class="flex justify-end gap-3">
                    <button data-accion="cancelar" class="px-4 py-2 text-slate-300 hover:text-white font-bold text-sm transition-colors">${escaparHTML(cancelarTexto)}</button>
                    <button data-accion="confirmar" class="px-4 py-2 ${danger ? 'bg-red-600 hover:bg-red-500' : 'bg-indigo-600 hover:bg-indigo-500'} text-white font-bold text-sm rounded-xl transition-colors">${escaparHTML(confirmarTexto)}</button>
                </div>
            </div>`;
        document.body.appendChild(overlay);

        const cerrar = (resultado) => {
            overlay.remove();
            resolve(resultado);
        };

        overlay.querySelector('[data-accion="confirmar"]').addEventListener('click', () => cerrar(true));
        overlay.querySelector('[data-accion="cancelar"]').addEventListener('click', () => cerrar(false));
        overlay.querySelector('.absolute.inset-0').addEventListener('click', () => cerrar(false));

        const onEsc = (e) => {
            if (e.key === 'Escape') { cerrar(false); document.removeEventListener('keydown', onEsc); }
        };
        document.addEventListener('keydown', onEsc);
    });
}

/**
 * Muestra un modal para reportar contenido inapropiado: pide un motivo breve
 * y devuelve una Promesa que resuelve con el texto del motivo, o null si la
 * persona canceló.
 * @param {{titulo?: string}} opciones
 * @returns {Promise<string|null>}
 */
export function showReportPrompt(opciones = {}) {
    const { titulo = '🚩 Reportar contenido' } = opciones;

    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'fixed inset-0 z-[250] flex items-center justify-center p-4';
        overlay.innerHTML = `
            <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
            <div class="relative w-full max-w-sm bg-[#0a0a0f] border border-red-500/30 rounded-2xl shadow-2xl p-6">
                <h3 class="text-lg font-black text-white mb-2">${escaparHTML(titulo)}</h3>
                <p class="text-sm text-slate-400 mb-3">Cuéntanos brevemente qué pasa. Un administrador lo revisará.</p>
                <textarea id="ui-utils-motivo-reporte" rows="3" maxlength="300" placeholder="Ej: contenido ofensivo, spam, suplantación..." class="w-full bg-slate-900 border border-slate-700 text-white px-3 py-2 rounded-xl outline-none focus:ring-2 focus:ring-red-500 resize-none mb-2"></textarea>
                <p id="ui-utils-error-reporte" class="hidden text-xs text-red-400 mb-2">Escribe brevemente el motivo antes de enviar.</p>
                <div class="flex justify-end gap-3 mt-2">
                    <button data-accion="cancelar" class="px-4 py-2 text-slate-300 hover:text-white font-bold text-sm transition-colors">Cancelar</button>
                    <button data-accion="confirmar" class="px-4 py-2 bg-red-600 hover:bg-red-500 text-white font-bold text-sm rounded-xl transition-colors">Enviar reporte</button>
                </div>
            </div>`;
        document.body.appendChild(overlay);

        const textarea = overlay.querySelector('#ui-utils-motivo-reporte');
        textarea.focus();

        const cerrar = (resultado) => {
            overlay.remove();
            resolve(resultado);
        };

        overlay.querySelector('[data-accion="confirmar"]').addEventListener('click', () => {
            const motivo = textarea.value.trim();
            if (!motivo) {
                overlay.querySelector('#ui-utils-error-reporte').classList.remove('hidden');
                return;
            }
            cerrar(motivo);
        });
        overlay.querySelector('[data-accion="cancelar"]').addEventListener('click', () => cerrar(null));
        overlay.querySelector('.absolute.inset-0').addEventListener('click', () => cerrar(null));

        const onEsc = (e) => {
            if (e.key === 'Escape') { cerrar(null); document.removeEventListener('keydown', onEsc); }
        };
        document.addEventListener('keydown', onEsc);
    });
}

/**
 * HTML de tarjetas "esqueleto" (pulso) para usar como placeholder mientras
 * carga una grilla de tarjetas (escuadrones, torneos, partidas...).
 */
export function skeletonCards(n = 3) {
    const tarjeta = `
        <div class="glass-panel rounded-2xl p-6 animate-pulse">
            <div class="flex items-center gap-4 mb-4">
                <div class="w-14 h-14 rounded-xl bg-slate-800"></div>
                <div class="flex-1 space-y-2">
                    <div class="h-4 bg-slate-800 rounded w-3/4"></div>
                    <div class="h-3 bg-slate-800 rounded w-1/3"></div>
                </div>
            </div>
            <div class="h-3 bg-slate-800 rounded w-full mb-2"></div>
            <div class="h-3 bg-slate-800 rounded w-5/6 mb-6"></div>
            <div class="flex justify-between items-center pt-4 border-t border-slate-800">
                <div class="h-3 bg-slate-800 rounded w-1/4"></div>
                <div class="h-8 bg-slate-800 rounded-lg w-1/3"></div>
            </div>
        </div>`;
    return tarjeta.repeat(n);
}

/**
 * HTML de filas "esqueleto" (pulso) para listas simples (solicitudes,
 * moderación de admin, mensajes de chat, etc.)
 */
export function skeletonRows(n = 3) {
    const fila = `
        <div class="flex justify-between items-center bg-slate-900/60 border border-slate-800 rounded-xl p-4 animate-pulse">
            <div class="space-y-2 flex-1">
                <div class="h-4 bg-slate-800 rounded w-1/2"></div>
                <div class="h-3 bg-slate-800 rounded w-1/3"></div>
            </div>
            <div class="h-8 bg-slate-800 rounded-lg w-20"></div>
        </div>`;
    return `<div class="space-y-3">${fila.repeat(n)}</div>`;
}
