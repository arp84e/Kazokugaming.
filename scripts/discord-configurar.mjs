// scripts/discord-configurar.mjs
// Monta el servidor de Discord de KazokuGaming: roles, categorías, canales,
// permisos, AutoMod (filtro), modo Comunidad, incorporación (cada persona elige
// sus juegos al entrar), textos de bienvenida/normas y una invitación permanente.
//
// Se lanza a mano desde GitHub: Actions → "Discord" → Run workflow → configurar.
// Es seguro repetirlo: SOLO CREA LO QUE FALTA, nunca borra ni renombra nada
// (los canales y roles se reconocen por su nombre).

import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { leerConfiguracion, crearCliente, PERMISOS as P, bits, TIPO_CANAL, sinMenciones } from './discord-api.mjs';
import { JUEGOS, DISCORD_JUEGOS_CON_CANAL } from '../comunidad.js';

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WEB = 'https://www.kazokugaming.com';
const MOTIVO = 'Configuración automática de KazokuGaming';
const COLOR = 0x6366f1; // índigo de la web

// ============================================================
// ESTRUCTURA DEL SERVIDOR
// ============================================================
const SOLO_LECTURA = 'solo-lectura';   // nadie escribe salvo el staff (y el bot)
const SOLO_STAFF = 'solo-staff';       // invisible para el resto
const SOLO_ROL_JUEGO = 'solo-rol';     // visible solo para quien tenga el rol del juego

const slug = (t) => t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

function estructura() {
    const juegosConCanal = DISCORD_JUEGOS_CON_CANAL.map((v) => JUEGOS.find((j) => j.valor === v)).filter(Boolean);
    return [
        { categoria: '📌 BIENVENIDA', canales: [
            { nombre: 'bienvenida', tema: `Empieza aquí. La web de la comunidad: ${WEB}`, acceso: SOLO_LECTURA },
            { nombre: 'normas', tema: 'Las normas de la familia. Léelas antes de escribir.', acceso: SOLO_LECTURA },
            { nombre: 'anuncios', tema: 'Novedades, torneos y eventos de KazokuGaming.', acceso: SOLO_LECTURA },
            { nombre: 'roles', tema: 'Cómo elegir tus juegos para ver sus canales.', acceso: SOLO_LECTURA }
        ] },
        { categoria: '💬 COMUNIDAD', canales: [
            { nombre: 'general', tema: 'Charla libre de la familia gamer.' },
            { nombre: 'presentaciones', tema: 'Preséntate: quién eres, a qué juegas y qué buscas.' },
            { nombre: 'buscar-equipo', tema: `Busca gente para jugar ahora. Las partidas nuevas de ${WEB} aparecen aquí solas.`, lentitud: 30 },
            { nombre: 'clips-y-capturas', tema: 'Tus mejores jugadas, logros y momentos.' },
            { nombre: 'sugerencias', tema: 'Ideas para mejorar la web y el servidor.' }
        ] },
        { categoria: '🎮 JUEGOS', canales: juegosConCanal.map((j) => ({
            nombre: slug(j.nombre === 'League of Legends' ? 'lol' : j.nombre === 'EA SPORTS FC' ? 'ea-fc' : j.nombre),
            tema: `Todo sobre ${j.nombre}. Busca equipo y comparte. Página del juego: ${WEB}/juego-${j.slug}.html`,
            acceso: SOLO_ROL_JUEGO, juego: j.valor
        })) },
        { categoria: '🏆 TORNEOS Y EVENTOS', canales: [
            { nombre: 'torneos', tema: `Torneos de la comunidad. Inscripciones en ${WEB}/torneos.html`, acceso: SOLO_LECTURA },
            { nombre: 'agenda-semanal', tema: 'Quedadas fijas de cada semana. Aquí avisamos antes de empezar.', acceso: SOLO_LECTURA }
        ] },
        { categoria: '🔊 VOZ', canales: [
            { nombre: '🔊 Sala común', voz: true },
            { nombre: '🎮 Partida 1', voz: true, limite: 5 },
            { nombre: '🎮 Partida 2', voz: true, limite: 5 },
            { nombre: '🎮 Partida 3', voz: true, limite: 5 },
            { nombre: '🏆 Torneo', voz: true, acceso: 'voz-cerrada' },
            { nombre: '💤 AFK', voz: true, afk: true }
        ] },
        { categoria: '🛡️ STAFF', acceso: SOLO_STAFF, canales: [
            { nombre: 'moderacion', tema: 'Canal privado del equipo de moderación.' },
            { nombre: 'registro', tema: 'Avisos automáticos del filtro (AutoMod).' }
        ] }
    ];
}

const ROLES = [
    // nombre, color, se muestra aparte en la lista de miembros, se puede mencionar, permisos extra
    { nombre: '👑 Fundador', color: 0xf59e0b, separado: true },
    { nombre: '🛡️ Moderador', color: 0x10b981, separado: true, permisos: bits(P.EXPULSAR, P.BANEAR, P.VER_REGISTRO, P.GESTIONAR_MENSAJES, P.SILENCIAR, P.MOVER, P.GESTIONAR_APODOS, P.GESTIONAR_HILOS, P.AISLAR) },
    { nombre: '🏆 Campeón', color: 0xd946ef, separado: true },
    { nombre: '📺 Streamer', color: 0x9146ff, separado: true },
    ...JUEGOS.map((j) => ({ nombre: j.nombre, color: 0x94a3b8, mencionable: true, juego: j.valor }))
];

// ============================================================
// TEXTOS
// ============================================================
const TEXTO_BIENVENIDA = {
    title: '¡Bienvenido a la familia KazokuGaming! 🎮',
    description: [
        'Aquí nadie juega solo. Somos una comunidad gamer en español para encontrar compañeros, formar escuadrones y competir en torneos, siempre con buen rollo.',
        '',
        '**Cómo empezar**',
        '1️⃣ Lee las normas en <#NORMAS>.',
        '2️⃣ Elige tus juegos en **Canales y roles** (arriba del todo, en la lista de canales) para ver sus canales.',
        '3️⃣ Preséntate en <#PRESENTACIONES>.',
        '4️⃣ ¿Quieres jugar ya? Escribe en <#BUSCAR> o publica tu partida en la web.',
        '',
        `🌐 **La web:** ${WEB}`,
        'Allí creas tu perfil gratis, fundas tu escuadrón, te inscribes en torneos y escribes en el Muro. Las partidas y torneos nuevos de la web aparecen aquí automáticamente.'
    ].join('\n'),
    color: COLOR,
    url: WEB
};

const TEXTO_NORMAS = {
    title: '📜 Normas de la familia',
    description: [
        '**1. Respeto ante todo.** Nada de insultos, acoso, amenazas ni humillaciones. Se puede perder una partida sin perder las formas.',
        '**2. Cero odio.** No se tolera el racismo, el machismo, la homofobia ni ningún tipo de discriminación.',
        '**3. Nada de contenido sexual ni violento explícito.** Ni en mensajes, ni en imágenes, ni en apodos o avatares.',
        '**4. Sin spam ni publicidad.** No se hacen promociones, enlaces de referidos ni mensajes repetidos. Para colaboraciones, habla con el staff.',
        '**5. Juego limpio.** Prohibido compartir o vender trampas, cuentas o métodos para saltarse las normas de los juegos.',
        '**6. Protege tus datos.** No compartas contraseñas, teléfonos ni direcciones, ni los de nadie. Nadie del staff te pedirá nunca tu contraseña.',
        '**7. Cada cosa en su canal.** Busca equipo en <#BUSCAR>, los clips en <#CLIPS> y la charla libre en <#GENERAL>.',
        '**8. Haz caso al staff.** Si tienes un problema con alguien, no lo discutas en público: avisa a un 🛡️ Moderador.',
        '',
        'Saltarse las normas puede suponer un aviso, un silencio temporal o la expulsión, según la gravedad.',
        `Estas normas también se aplican en la web: ${WEB}`
    ].join('\n'),
    color: COLOR
};

const TEXTO_ROLES = {
    title: '🎮 Elige tus juegos',
    description: [
        'Pulsa **Canales y roles** (arriba del todo, en la lista de canales) y marca los juegos a los que juegas.',
        '',
        '• Verás los canales de esos juegos y desaparecerán los que no te interesan.',
        '• En <#BUSCAR> te avisaremos cuando alguien busque gente para tus juegos.',
        '• Puedes cambiarlos cuando quieras.',
        '',
        '**Roles especiales**',
        '🏆 **Campeón**: para quien gane un torneo de la comunidad.',
        '📺 **Streamer**: para quien transmita en Twitch. Pídeselo al staff.',
        '🛡️ **Moderador**: el equipo que cuida la comunidad.'
    ].join('\n'),
    color: COLOR
};

// AutoMod: palabras que se bloquean (las más graves; el resto lo cubren los moderadores).
// Admite comodines: "put*" bloquea puta, puto, putas...
const PALABRAS_PROHIBIDAS = [
    'hijueputa*', 'hijoputa*', 'hijodeputa*', 'malparid*', 'gilipollas', 'gonorrea', 'culero*',
    'maricon*', 'negrata*', 'sudaca*', 'subnormal*', 'retrasad*', 'mongolic*',
    'porno*', 'pornografia', 'hentai', 'onlyfans', 'nudes',
    'te voy a matar', 'te mato', 'ojala te mueras', 'suicidate'
];

// ============================================================
// LÓGICA
// ============================================================
async function main() {
    const cfg = leerConfiguracion();
    if (!cfg) return;
    const discord = crearCliente(cfg.token);
    const G = cfg.servidor;
    const hechos = [];
    const avisos = [];

    const bot = await discord('GET', '/users/@me');
    const servidor = await discord('GET', `/guilds/${G}`);
    console.log(`Servidor: ${servidor.name} · bot: ${bot.username}`);

    // ---------- Roles ----------
    let roles = await discord('GET', `/guilds/${G}/roles`);
    const rolPorNombre = new Map(roles.map((r) => [r.name, r]));
    for (const r of ROLES) {
        if (rolPorNombre.has(r.nombre)) continue;
        const creado = await discord('POST', `/guilds/${G}/roles`, {
            name: r.nombre, color: r.color, hoist: !!r.separado, mentionable: !!r.mencionable, permissions: r.permisos || '0'
        }, { motivo: MOTIVO });
        rolPorNombre.set(r.nombre, creado);
        hechos.push(`rol ${r.nombre}`);
    }
    const idRol = (nombre) => rolPorNombre.get(nombre)?.id;
    const rolDeJuego = (valor) => idRol(JUEGOS.find((j) => j.valor === valor)?.nombre);
    const MOD = idRol('🛡️ Moderador');

    // ---------- Permisos por tipo de acceso ----------
    const todos = G; // el rol @everyone tiene el mismo ID que el servidor
    const permisosDe = (acceso, extra = {}) => {
        const lista = [];
        if (acceso === SOLO_LECTURA) {
            lista.push({ id: todos, type: 0, allow: bits(P.VER_CANAL, P.LEER_HISTORIAL, P.REACCIONAR), deny: bits(P.ENVIAR_MENSAJES, P.CREAR_HILOS_PUBLICOS, P.ENVIAR_EN_HILOS) });
            if (MOD) lista.push({ id: MOD, type: 0, allow: bits(P.ENVIAR_MENSAJES), deny: '0' });
        } else if (acceso === SOLO_STAFF) {
            lista.push({ id: todos, type: 0, allow: '0', deny: bits(P.VER_CANAL) });
            if (MOD) lista.push({ id: MOD, type: 0, allow: bits(P.VER_CANAL, P.ENVIAR_MENSAJES, P.LEER_HISTORIAL), deny: '0' });
        } else if (acceso === SOLO_ROL_JUEGO) {
            lista.push({ id: todos, type: 0, allow: '0', deny: bits(P.VER_CANAL) });
            const rj = rolDeJuego(extra.juego);
            if (rj) lista.push({ id: rj, type: 0, allow: bits(P.VER_CANAL, P.ENVIAR_MENSAJES, P.LEER_HISTORIAL), deny: '0' });
            if (MOD) lista.push({ id: MOD, type: 0, allow: bits(P.VER_CANAL), deny: '0' });
        } else if (acceso === 'voz-cerrada') {
            lista.push({ id: todos, type: 0, allow: '0', deny: bits(P.CONECTAR) });
            if (MOD) lista.push({ id: MOD, type: 0, allow: bits(P.CONECTAR, P.HABLAR, P.MOVER), deny: '0' });
        }
        return lista;
    };

    // ---------- Categorías y canales ----------
    let canales = await discord('GET', `/guilds/${G}/channels`);
    const buscar = (nombre, tipo, padre) => canales.find((c) => c.name === nombre && c.type === tipo && (padre === undefined || c.parent_id === padre));
    const ids = {};
    let posicion = 0;
    for (const bloque of estructura()) {
        if (!bloque.canales.length) continue;
        let cat = buscar(bloque.categoria, TIPO_CANAL.CATEGORIA);
        if (!cat) {
            cat = await discord('POST', `/guilds/${G}/channels`, {
                name: bloque.categoria, type: TIPO_CANAL.CATEGORIA, position: posicion, permission_overwrites: permisosDe(bloque.acceso)
            }, { motivo: MOTIVO });
            canales.push(cat);
            hechos.push(`categoría ${bloque.categoria}`);
        }
        posicion++;
        for (const c of bloque.canales) {
            const tipo = c.voz ? TIPO_CANAL.VOZ : TIPO_CANAL.TEXTO;
            // Un canal con ese nombre en cualquier sitio cuenta como existente (así no duplicamos
            // los canales "general" que Discord crea por defecto: se reutilizan y se mueven aquí)
            let canal = buscar(c.nombre, tipo, cat.id) || buscar(c.nombre, tipo);
            const acceso = c.acceso || bloque.acceso;
            if (!canal) {
                canal = await discord('POST', `/guilds/${G}/channels`, {
                    name: c.nombre, type: tipo, parent_id: cat.id,
                    ...(c.tema ? { topic: c.tema } : {}),
                    ...(c.lentitud ? { rate_limit_per_user: c.lentitud } : {}),
                    ...(c.limite ? { user_limit: c.limite } : {}),
                    permission_overwrites: permisosDe(acceso, c)
                }, { motivo: MOTIVO });
                canales.push(canal);
                hechos.push(`canal ${c.voz ? '🔊' : '#'}${c.nombre}`);
            } else if (canal.parent_id !== cat.id) {
                canal = await discord('PATCH', `/channels/${canal.id}`, {
                    parent_id: cat.id, ...(c.tema ? { topic: c.tema } : {}), permission_overwrites: permisosDe(acceso, c)
                }, { motivo: MOTIVO });
                hechos.push(`canal #${c.nombre} movido a ${bloque.categoria}`);
            }
            ids[c.nombre] = canal.id;
            if (c.afk) ids.__afk = canal.id;
        }
    }

    // Canales de voz que Discord crea por defecto ("General" en "Canales de voz"): se dejan tal cual.

    // ---------- Ajustes del servidor y modo Comunidad ----------
    const ajustes = {
        verification_level: Math.max(servidor.verification_level ?? 0, 2),      // Medio: cuenta con más de 5 minutos
        explicit_content_filter: 2,                                              // analizar imágenes de todos
        default_message_notifications: 1,                                        // solo menciones (menos ruido)
        preferred_locale: 'es-ES',
        system_channel_id: ids.general,
        afk_channel_id: ids.__afk, afk_timeout: 900
    };
    if (!servidor.icon) {
        try {
            const icono = await readFile(path.join(RAIZ, 'icons', 'icon-512.png'));
            ajustes.icon = `data:image/png;base64,${icono.toString('base64')}`;
        } catch { /* sin icono, no pasa nada */ }
    }
    await discord('PATCH', `/guilds/${G}`, ajustes, { motivo: MOTIVO });
    hechos.push('ajustes de seguridad del servidor');

    let comunidad = (servidor.features || []).includes('COMMUNITY');
    if (!comunidad) {
        try {
            await discord('PATCH', `/guilds/${G}`, {
                features: [...new Set([...(servidor.features || []), 'COMMUNITY'])],
                rules_channel_id: ids.normas,
                public_updates_channel_id: ids.moderacion
            }, { motivo: MOTIVO });
            comunidad = true;
            hechos.push('modo Comunidad activado');
        } catch (e) {
            avisos.push(`No se pudo activar el modo Comunidad automáticamente (${e.status}). Hazlo a mano: Ajustes del servidor → Habilitar comunidad.`);
        }
    }

    // ---------- AutoMod (filtro automático) ----------
    try {
        const reglas = await discord('GET', `/guilds/${G}/auto-moderation/rules`);
        const existe = (nombre) => reglas.some((r) => r.name === nombre);
        const alertar = ids.registro ? [{ type: 2, metadata: { channel_id: ids.registro } }] : [];
        const exentos = [MOD, idRol('👑 Fundador')].filter(Boolean);
        const nuevas = [
            { name: 'Kazoku · Lenguaje grave', trigger_type: 1, trigger_metadata: { keyword_filter: PALABRAS_PROHIBIDAS, allow_list: [] },
              actions: [{ type: 1, metadata: { custom_message: 'Tu mensaje no se envió porque incumple las normas de la comunidad. Revisa #normas.' } }, ...alertar] },
            { name: 'Kazoku · Spam', trigger_type: 3, trigger_metadata: {}, actions: [{ type: 1, metadata: {} }, ...alertar] },
            { name: 'Kazoku · Menciones masivas', trigger_type: 5, trigger_metadata: { mention_total_limit: 5, mention_raid_protection_enabled: true },
              actions: [{ type: 1, metadata: {} }, ...alertar] },
            { name: 'Kazoku · Contenido sexual e insultos (lista de Discord)', trigger_type: 4, trigger_metadata: { presets: [1, 2, 3] },
              actions: [{ type: 1, metadata: {} }] }
        ];
        for (const r of nuevas) {
            if (existe(r.name) || (r.trigger_type !== 1 && reglas.some((x) => x.trigger_type === r.trigger_type))) continue;
            try {
                await discord('POST', `/guilds/${G}/auto-moderation/rules`, { ...r, event_type: 1, enabled: true, exempt_roles: exentos }, { motivo: MOTIVO });
                hechos.push(`AutoMod: ${r.name}`);
            } catch (e) {
                avisos.push(`AutoMod "${r.name}" no se pudo crear (${e.status}).`);
            }
        }
    } catch (e) {
        avisos.push(`No se pudo configurar AutoMod (${e.status}). Puedes activarlo a mano en Ajustes del servidor → AutoMod.`);
    }

    // ---------- Incorporación: elegir juegos al entrar (requiere modo Comunidad) ----------
    if (comunidad) {
        try {
            const actual = await discord('GET', `/guilds/${G}/onboarding`);
            if (!actual?.enabled) {
                const opciones = JUEGOS.map((j) => {
                    const rol = rolDeJuego(j.valor);
                    const canalJuego = estructura().flatMap((b) => b.canales).find((c) => c.juego === j.valor);
                    return rol ? { id: String(BigInt(G) + BigInt(JUEGOS.indexOf(j) + 1)), title: j.nombre, description: j.genero, role_ids: [rol], channel_ids: canalJuego && ids[canalJuego.nombre] ? [ids[canalJuego.nombre]] : [] } : null;
                }).filter(Boolean);
                const porDefecto = ['bienvenida', 'normas', 'anuncios', 'roles', 'general', 'presentaciones', 'buscar-equipo', 'clips-y-capturas', 'sugerencias', 'torneos', 'agenda-semanal'].map((n) => ids[n]).filter(Boolean);
                await discord('PUT', `/guilds/${G}/onboarding`, {
                    prompts: [{ id: String(BigInt(G) + 100n), type: 0, title: '¿A qué juegas?', single_select: false, required: false, in_onboarding: true, options: opciones }],
                    default_channel_ids: porDefecto,
                    enabled: true,
                    mode: 0
                }, { motivo: MOTIVO });
                hechos.push('incorporación: elegir juegos al entrar');
            }
        } catch (e) {
            avisos.push(`La incorporación (elegir juegos al entrar) no se pudo activar automáticamente (${e.status}). Hazlo a mano: Ajustes del servidor → Incorporación → pregunta "¿A qué juegas?" con un rol por juego.`);
        }
    }

    // ---------- Textos de bienvenida, normas y roles (solo si el bot aún no escribió) ----------
    const reemplazar = (t) => t.replace('<#NORMAS>', `<#${ids.normas}>`).replace('<#PRESENTACIONES>', `<#${ids.presentaciones}>`)
        .replace(/<#BUSCAR>/g, `<#${ids['buscar-equipo']}>`).replace('<#CLIPS>', `<#${ids['clips-y-capturas']}>`).replace('<#GENERAL>', `<#${ids.general}>`);
    for (const [canal, embed] of [['bienvenida', TEXTO_BIENVENIDA], ['normas', TEXTO_NORMAS], ['roles', TEXTO_ROLES]]) {
        if (!ids[canal]) continue;
        const mensajes = await discord('GET', `/channels/${ids[canal]}/messages?limit=20`);
        if (mensajes.some((m) => m.author?.id === bot.id)) continue;
        await discord('POST', `/channels/${ids[canal]}/messages`, { embeds: [{ ...embed, description: reemplazar(embed.description) }], allowed_mentions: sinMenciones() });
        hechos.push(`texto en #${canal}`);
    }

    // ---------- Invitación permanente (para la web) ----------
    let invitacion = null;
    try {
        const existentes = await discord('GET', `/guilds/${G}/invites`);
        invitacion = existentes.find((i) => i.inviter?.id === bot.id && i.max_age === 0 && i.max_uses === 0 && i.channel?.id === ids.bienvenida);
        if (!invitacion && ids.bienvenida) {
            invitacion = await discord('POST', `/channels/${ids.bienvenida}/invites`, { max_age: 0, max_uses: 0, unique: false, temporary: false }, { motivo: MOTIVO });
            hechos.push('invitación permanente');
        }
    } catch (e) {
        avisos.push(`No se pudo crear la invitación (${e.status}). Créala a mano: clic derecho en el servidor → Invitar gente → Caducidad: Nunca.`);
    }

    // ---------- Resumen ----------
    const enlace = invitacion ? `https://discord.gg/${invitacion.code}` : null;
    const resumen = [
        '## Discord configurado',
        hechos.length ? hechos.map((h) => `- ✅ ${h}`).join('\n') : '- Todo estaba ya creado: no hubo cambios.',
        avisos.length ? '\n### Pendiente de hacer a mano\n' + avisos.map((a) => `- ⚠️ ${a}`).join('\n') : '',
        enlace ? `\n### Invitación permanente\n${enlace}\n\nPégala en DISCORD_INVITE de comunidad.js (o pásasela a Claude).` : ''
    ].join('\n');
    console.log(resumen);
    if (process.env.GITHUB_STEP_SUMMARY) {
        const { appendFile } = await import('node:fs/promises');
        await appendFile(process.env.GITHUB_STEP_SUMMARY, resumen + '\n');
    }
}

main().catch((e) => {
    // Nunca imprimimos la clave: el error solo lleva la ruta y la respuesta de Discord
    console.error('❌', e.message);
    if (e.status === 401) console.error('La clave del bot (DISCORD_BOT_TOKEN) no es válida. Genera una nueva en el portal de desarrolladores y actualiza el secreto.');
    if (e.status === 403) console.error('El bot no tiene permisos suficientes. Invítalo de nuevo con el permiso "Administrador" (ver SETUP.md, sección 19).');
    if (e.status === 404) console.error('No se encontró el servidor: revisa DISCORD_SERVIDOR_ID y que el bot esté dentro del servidor.');
    process.exitCode = 1;
});
