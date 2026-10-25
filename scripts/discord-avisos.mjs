// scripts/discord-avisos.mjs
// Lo ejecuta GitHub Actions cada 15 minutos (.github/workflows/discord.yml).
// Publica en Discord, sin duplicar nunca:
//   • #anuncios      → cada torneo nuevo de la web
//   • #buscar-equipo → cada partida nueva de la web (mencionando el rol de ese juego)
//   • #agenda-semanal→ recordatorio ~1 hora antes de cada quedada de AGENDA_SEMANAL
//
// Lee de Firestore SOLO lo que ya es público en la web (torneos y partidas),
// con la misma clave pública que usa la web: no necesita contraseñas de Firebase.
// Para no repetir avisos, mira los últimos mensajes del bot en cada canal
// (cada aviso lleva su identificador en el pie).

import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { leerConfiguracion, crearCliente, escaparMarkdown, sinMenciones } from './discord-api.mjs';
import { JUEGOS, AGENDA_SEMANAL, proximaOcurrencia, DISCORD_MENCIONAR_ROL_DEL_JUEGO } from '../comunidad.js';

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WEB = 'https://www.kazokugaming.com';
const VENTANA_MS = 24 * 3600 * 1000;   // solo avisamos de lo creado en las últimas 24 h
const MAX_POR_CANAL = 8;               // nunca más de 8 avisos por canal en una pasada
const RECORDATORIO_MS = 75 * 60 * 1000; // recordar la agenda cuando falte menos de 1 h 15 min

// ---------- Firestore (lectura pública por REST) ----------
async function configFirebase() {
    const js = await readFile(path.join(RAIZ, 'firebase-init.js'), 'utf8');
    const apiKey = js.match(/apiKey:\s*"([^"]+)"/)?.[1];
    const projectId = js.match(/projectId:\s*"([^"]+)"/)?.[1];
    if (!apiKey || !projectId) throw new Error('No se encontró la configuración de Firebase en firebase-init.js');
    return { apiKey, projectId };
}

function valor(v) {
    if (!v || typeof v !== 'object') return undefined;
    if ('stringValue' in v) return v.stringValue;
    if ('integerValue' in v) return Number(v.integerValue);
    if ('doubleValue' in v) return v.doubleValue;
    if ('booleanValue' in v) return v.booleanValue;
    if ('timestampValue' in v) return Date.parse(v.timestampValue);
    if ('nullValue' in v) return null;
    if ('arrayValue' in v) return (v.arrayValue.values || []).map(valor);
    if ('mapValue' in v) return Object.fromEntries(Object.entries(v.mapValue.fields || {}).map(([k, x]) => [k, valor(x)]));
    return undefined;
}

async function recientes(fb, coleccion, desdeMs) {
    const url = `https://firestore.googleapis.com/v1/projects/${fb.projectId}/databases/(default)/documents:runQuery?key=${fb.apiKey}`;
    const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Referer': `${WEB}/` }, // por si la clave está restringida por dominio
        body: JSON.stringify({ structuredQuery: {
            from: [{ collectionId: coleccion }],
            where: { fieldFilter: { field: { fieldPath: 'creadoEn' }, op: 'GREATER_THAN', value: { timestampValue: new Date(desdeMs).toISOString() } } },
            orderBy: [{ field: { fieldPath: 'creadoEn' }, direction: 'ASCENDING' }],
            limit: 30
        } }),
        signal: AbortSignal.timeout(20000)
    });
    if (!resp.ok) throw new Error(`Firestore (${coleccion}) respondió ${resp.status}: ${(await resp.text()).slice(0, 300)}`);
    return (await resp.json())
        .filter((x) => x.document)
        .map((x) => ({ id: x.document.name.split('/').pop(), ...Object.fromEntries(Object.entries(x.document.fields || {}).map(([k, v]) => [k, valor(v)])) }));
}

// ---------- Discord ----------
const PIE = (clave) => `KazokuGaming · ${clave}`;

async function clavesYaPublicadas(discord, canalId, botId) {
    const mensajes = await discord('GET', `/channels/${canalId}/messages?limit=100`);
    const claves = new Set();
    for (const m of mensajes) {
        if (m.author?.id !== botId) continue;
        for (const e of m.embeds || []) {
            const t = e.footer?.text || '';
            if (t.startsWith('KazokuGaming · ')) claves.add(t.slice('KazokuGaming · '.length));
        }
    }
    return claves;
}

const unix = (ms) => Math.floor(ms / 1000);
const juegoDe = (v) => JUEGOS.find((j) => j.valor === v) || null;

function embedTorneo(t) {
    const juego = juegoDe(t.juego);
    const campos = [];
    if (t.fecha) campos.push({ name: '📅 Cuándo', value: `<t:${unix(t.fecha)}:F> (<t:${unix(t.fecha)}:R>)`, inline: false });
    if (t.formato) campos.push({ name: '⚔️ Formato', value: escaparMarkdown(t.formato, 200), inline: true });
    if (t.cupoMax) campos.push({ name: '👥 Cupo', value: String(Number(t.cupoMax) || '—'), inline: true });
    if (t.recompensa) campos.push({ name: '🎁 Premio', value: escaparMarkdown(t.recompensa, 200), inline: true });
    return {
        title: `🏆 Nuevo torneo: ${escaparMarkdown(t.titulo || 'Torneo', 200)}`,
        description: `${juego ? `**${escaparMarkdown(juego.nombre)}** · ` : ''}Inscríbete gratis en la web antes de que se llene el cupo.`,
        url: `${WEB}/torneos.html`,
        color: 0xd946ef,
        fields: campos,
        footer: { text: PIE(`torneo:${t.id}`) },
        timestamp: new Date(t.creadoEn || Date.now()).toISOString()
    };
}

function embedPartida(p) {
    const juego = juegoDe(p.juego);
    return {
        title: `🎮 ${escaparMarkdown(juego ? juego.nombre : (p.juego || 'Partida'), 100)} · ${escaparMarkdown(p.nivel || 'Busca equipo', 100)}`,
        description: escaparMarkdown(p.mensaje || 'Buscando gente para jugar.', 500),
        url: juego ? `${WEB}/juego-${juego.slug}.html` : `${WEB}/#grupos-buscando-gente`,
        color: 0x6366f1,
        fields: [
            { name: '👥 Buscan', value: `${Number(p.espacios) || 1} más`, inline: true },
            { name: '🙋 Lo organiza', value: escaparMarkdown(p.autorNombre || 'Un miembro', 64), inline: true },
            { name: '➡️ Unirse', value: `[Saludar y unirse en la web](${WEB}/#grupos-buscando-gente)`, inline: false }
        ],
        footer: { text: PIE(`partida:${p.id}`) },
        timestamp: new Date(p.creadoEn || Date.now()).toISOString()
    };
}

function embedAgenda(ev, cuando) {
    const juego = juegoDe(ev.juego);
    return {
        title: `⏰ Hoy: ${escaparMarkdown(ev.titulo || ev.juego, 150)}`,
        description: `${ev.descripcion ? escaparMarkdown(ev.descripcion, 300) + '\n\n' : ''}Empieza <t:${unix(cuando.getTime())}:R> (<t:${unix(cuando.getTime())}:t>). ¡Pásate por la sala de voz y no juegues solo!`,
        url: juego ? `${WEB}/juego-${juego.slug}.html` : WEB,
        color: 0x10b981,
        footer: { text: PIE(`agenda:${ev.dia}-${ev.hora}-${cuando.toISOString().slice(0, 10)}`) }
    };
}

async function main() {
    const cfg = leerConfiguracion();
    if (!cfg) return;
    const discord = crearCliente(cfg.token);
    const G = cfg.servidor;

    const bot = await discord('GET', '/users/@me');
    const canales = await discord('GET', `/guilds/${G}/channels`);
    const canal = (n) => canales.find((c) => c.name === n && c.type === 0)?.id;
    const roles = await discord('GET', `/guilds/${G}/roles`);
    const rolDeJuego = (v) => roles.find((r) => r.name === juegoDe(v)?.nombre)?.id;

    const fb = await configFirebase();
    const desde = Date.now() - VENTANA_MS;
    let publicados = 0;

    async function publicar(nombreCanal, elementos, clave, construir, mencion) {
        const id = canal(nombreCanal);
        if (!id) { console.warn(`⚠️ No existe #${nombreCanal}: lanza primero "configurar".`); return; }
        if (!elementos.length) return;
        const ya = await clavesYaPublicadas(discord, id, bot.id);
        const pendientes = elementos.filter((e) => !ya.has(clave(e))).slice(0, MAX_POR_CANAL);
        for (const e of pendientes) {
            const rol = mencion ? mencion(e) : null;
            await discord('POST', `/channels/${id}/messages`, {
                ...(rol ? { content: `<@&${rol}>` } : {}),
                embeds: [construir(e)],
                allowed_mentions: sinMenciones(rol ? [rol] : [])
            });
            publicados++;
        }
        console.log(`#${nombreCanal}: ${pendientes.length} aviso(s) nuevo(s)`);
    }

    // 1) Torneos nuevos
    try {
        const torneos = await recientes(fb, 'torneos', desde);
        await publicar('anuncios', torneos, (t) => `torneo:${t.id}`, embedTorneo);
    } catch (e) { console.warn('⚠️ Torneos:', e.message); }

    // 2) Partidas nuevas
    try {
        const partidas = await recientes(fb, 'partidas', desde);
        await publicar('buscar-equipo', partidas, (p) => `partida:${p.id}`, embedPartida,
            DISCORD_MENCIONAR_ROL_DEL_JUEGO ? (p) => rolDeJuego(p.juego) : null);
    } catch (e) { console.warn('⚠️ Partidas:', e.message); }

    // 3) Recordatorios de la agenda semanal
    const ahora = Date.now();
    const proximos = AGENDA_SEMANAL
        .map((ev) => ({ ev, cuando: proximaOcurrencia(ev) }))
        .filter(({ cuando }) => cuando && cuando.getTime() > ahora && cuando.getTime() - ahora <= RECORDATORIO_MS);
    await publicar('agenda-semanal', proximos, ({ ev, cuando }) => `agenda:${ev.dia}-${ev.hora}-${cuando.toISOString().slice(0, 10)}`,
        ({ ev, cuando }) => embedAgenda(ev, cuando), ({ ev }) => rolDeJuego(ev.juego));

    console.log(`Listo: ${publicados} aviso(s) publicados.`);
}

main().catch((e) => {
    console.error('❌', e.message);
    if (e.status === 401) console.error('La clave del bot (DISCORD_BOT_TOKEN) no es válida.');
    if (e.status === 403) console.error('El bot no tiene permiso para escribir en ese canal.');
    process.exitCode = 1;
});
