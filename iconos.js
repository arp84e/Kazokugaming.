// iconos.js
// Set pequeño de iconos SVG en línea, estilo minimalista (stroke, sin relleno),
// para usar en la navegación y encabezados en vez de emojis — los emojis se
// ven distinto en cada sistema operativo; estos iconos son siempre iguales.
//
// Cada función devuelve una cadena <svg>...</svg> lista para insertar en un
// template literal. Todas usan currentColor, así que heredan el color del
// texto que las rodea (cambian solo con clases de Tailwind como text-white).

const base = (contenido, extraClase = '') =>
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline-block w-[1em] h-[1em] align-[-0.15em] ${extraClase}">${contenido}</svg>`;

export const iconoInicio = (c) => base('<path d="M3 9.5 12 3l9 6.5"/><path d="M5 10v10a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V10"/>', c);
export const iconoEscudo = (c) => base('<path d="M12 3 4 6v6c0 4.5 3.2 7.9 8 9 4.8-1.1 8-4.5 8-9V6l-8-3Z"/>', c);
export const iconoTrofeo = (c) => base('<path d="M8 4h8v4a4 4 0 0 1-8 0V4Z"/><path d="M8 5H5a2 2 0 0 0 2 4"/><path d="M16 5h3a2 2 0 0 1-2 4"/><path d="M12 12v3"/><path d="M9 20h6"/><path d="M10 15h4l1 5H9l1-5Z"/>', c);
export const iconoUsuario = (c) => base('<circle cx="12" cy="8" r="3.5"/><path d="M5 20c0-3.5 3.1-6 7-6s7 2.5 7 6"/>', c);
export const iconoCampana = (c) => base('<path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6Z"/><path d="M10 20a2 2 0 0 0 4 0"/>', c);
export const iconoBuscar = (c) => base('<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>', c);
export const iconoCerrar = (c) => base('<path d="M6 6l12 12M18 6 6 18"/>', c);
