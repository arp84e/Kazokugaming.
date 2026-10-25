// scripts/discord-api.mjs
// Funciones comunes para hablar con la API oficial de Discord desde GitHub
// Actions. La clave del bot llega SOLO por la variable de entorno
// DISCORD_BOT_TOKEN (un "secreto" de GitHub): nunca se escribe en el código,
// en los registros ni en el repositorio.

const API = 'https://discord.com/api/v10';

export const PERMISOS = {
    CREAR_INVITACION: 1n << 0n,
    EXPULSAR: 1n << 1n,
    BANEAR: 1n << 2n,
    VER_REGISTRO: 1n << 7n,
    REACCIONAR: 1n << 6n,
    VER_CANAL: 1n << 10n,
    ENVIAR_MENSAJES: 1n << 11n,
    GESTIONAR_MENSAJES: 1n << 13n,
    INSERTAR_ENLACES: 1n << 14n,
    ADJUNTAR_ARCHIVOS: 1n << 15n,
    LEER_HISTORIAL: 1n << 16n,
    MENCIONAR_TODOS: 1n << 17n,
    CONECTAR: 1n << 20n,
    HABLAR: 1n << 21n,
    SILENCIAR: 1n << 22n,
    MOVER: 1n << 24n,
    GESTIONAR_APODOS: 1n << 27n,
    GESTIONAR_HILOS: 1n << 34n,
    CREAR_HILOS_PUBLICOS: 1n << 35n,
    ENVIAR_EN_HILOS: 1n << 38n,
    AISLAR: 1n << 40n
};
export const bits = (...lista) => lista.reduce((a, b) => a | b, 0n).toString();

export const TIPO_CANAL = { TEXTO: 0, VOZ: 2, CATEGORIA: 4 };

export function leerConfiguracion() {
    const token = (process.env.DISCORD_BOT_TOKEN || '').trim();
    const servidor = (process.env.DISCORD_SERVIDOR_ID || '').trim();
    if (!token || !servidor) {
        console.log('ℹ️  Faltan los secretos DISCORD_BOT_TOKEN y/o DISCORD_SERVIDOR_ID en GitHub. No se hace nada (ver SETUP.md, sección 19).');
        return null;
    }
    if (!/^\d{15,22}$/.test(servidor)) throw new Error('DISCORD_SERVIDOR_ID no parece un ID de servidor válido (solo números).');
    return { token, servidor };
}

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

// Llamada a la API con reintentos cuando Discord pide ir más despacio (429)
export function crearCliente(token) {
    return async function discord(metodo, ruta, cuerpo, { reintentos = 5, motivo } = {}) {
        for (let intento = 0; ; intento++) {
            const resp = await fetch(API + ruta, {
                method: metodo,
                headers: {
                    'Authorization': `Bot ${token}`,
                    'Content-Type': 'application/json',
                    'User-Agent': 'DiscordBot (https://www.kazokugaming.com, 1.0)',
                    ...(motivo ? { 'X-Audit-Log-Reason': encodeURIComponent(motivo) } : {})
                },
                body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo)
            });
            if (resp.status === 429 && intento < reintentos) {
                const datos = await resp.json().catch(() => ({}));
                await esperar(Math.ceil((datos.retry_after ?? 1) * 1000) + 250);
                continue;
            }
            if (resp.status === 204) return null;
            const texto = await resp.text();
            let datos = null;
            try { datos = texto ? JSON.parse(texto) : null; } catch { datos = texto; }
            if (!resp.ok) {
                const error = new Error(`Discord ${metodo} ${ruta} → ${resp.status}: ${typeof datos === 'object' ? JSON.stringify(datos).slice(0, 400) : String(datos).slice(0, 400)}`);
                error.status = resp.status;
                error.datos = datos;
                throw error;
            }
            return datos;
        }
    };
}

// Escapa el formato de Discord (negritas, enlaces enmascarados, citas...) en
// textos que escribieron los usuarios de la web.
export function escaparMarkdown(texto, max = 1000) {
    let t = String(texto ?? '').replace(/[\\*_`~|>\[\]()#-]/g, (c) => '\\' + c).replace(/@/g, '@​');
    if (t.length > max) t = t.slice(0, max - 1) + '…';
    return t;
}

// Nunca mencionar a nadie salvo lo que se indique expresamente
export const sinMenciones = (roles = []) => ({ parse: [], roles });
