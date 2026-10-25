// comunidad.js
// ============================================================
// CONFIGURACIÓN DE LA COMUNIDAD — edita este archivo para cambiar
// lo que se muestra en la portada y en las páginas de cada juego.
// No hace falta tocar nada más: todo lo que está vacío se oculta solo.
// ============================================================

// ---------- 1. Enlace de invitación a tu servidor de Discord ----------
// Pega aquí tu invitación permanente (Discord → tu servidor → Invitar gente →
// "Editar enlace de invitación" → Caducidad: Nunca). Ejemplo:
//   export const DISCORD_INVITE = 'https://discord.gg/abc123';
// Mientras esté vacío, los botones de Discord no aparecen.
export const DISCORD_INVITE = '';

// ---------- 2. Agenda semanal (eventos fijos de la comunidad) ----------
// Quedadas que se repiten cada semana, para que siempre haya algo a lo que
// unirse aunque todavía haya pocas partidas. SOLO pon eventos que vayas a
// organizar de verdad (tú o alguien de confianza): si alguien llega y no hay
// nadie, pierde la confianza en la comunidad.
//   dia: 0 = domingo, 1 = lunes, ... 5 = viernes, 6 = sábado
//   hora: 'HH:MM' en hora de España peninsular (Europe/Madrid)
//   juego: debe coincidir con el "valor" de un juego de la lista JUEGOS
// Ejemplos (quita las // del principio para activarlos):
export const AGENDA_SEMANAL = [
    // { dia: 5, hora: '21:00', juego: 'Fortnite', titulo: 'Viernes de Fortnite', descripcion: 'Escuadrones abiertos para todos los niveles.' },
    // { dia: 0, hora: '18:00', juego: 'EA FC', titulo: 'Domingo de EA FC', descripcion: 'Partidos amistosos en Clubs. Trae tu mejor once.' },
];
export const ZONA_HORARIA_AGENDA = 'Europe/Madrid';

// ---------- 3. Streamers de la comunidad ----------
// Canales de Twitch de miembros que transmiten. Solo el nombre del canal
// (lo que va después de twitch.tv/). Ejemplo:
//   { nombre: 'ShadowNinja', canal: 'shadowninja99', juego: 'Valorant' },
export const STREAMERS = [
];

// ---------- 4. Contadores de la portada ----------
// Un contador solo se muestra cuando supera su mínimo: "3 jugadores" junto a
// "comunidad gamer" juega en contra; "250 jugadores" juega a favor.
export const UMBRALES_ESTADISTICAS = {
    escuadrones: 10,
    torneos: 3,
    jugadores: 50
};

// ---------- 5. Juegos de la comunidad ----------
// "valor" es lo que se guarda en Firestore (no lo cambies en juegos que ya
// tienen escuadrones/partidas). "slug" es el nombre de su página: juego-<slug>.html
export const JUEGOS = [
    { valor: 'Valorant', nombre: 'Valorant', slug: 'valorant', genero: 'Shooter táctico 5v5', degradado: 'from-red-500 to-rose-700', sigla: 'VA' },
    { valor: 'League of Legends', nombre: 'League of Legends', slug: 'league-of-legends', genero: 'MOBA 5v5', degradado: 'from-blue-500 to-indigo-700', sigla: 'LoL' },
    { valor: 'Call of Duty', nombre: 'Call of Duty: Warzone', slug: 'call-of-duty', genero: 'Battle royale', degradado: 'from-amber-500 to-orange-700', sigla: 'CoD' },
    { valor: 'Minecraft', nombre: 'Minecraft', slug: 'minecraft', genero: 'Sandbox y supervivencia', degradado: 'from-green-500 to-emerald-700', sigla: 'MC' },
    { valor: 'Fortnite', nombre: 'Fortnite', slug: 'fortnite', genero: 'Battle royale', degradado: 'from-violet-500 to-purple-700', sigla: 'FN' },
    { valor: 'Free Fire', nombre: 'Free Fire', slug: 'free-fire', genero: 'Battle royale móvil', degradado: 'from-orange-500 to-red-700', sigla: 'FF' },
    { valor: 'EA FC', nombre: 'EA SPORTS FC', slug: 'ea-fc', genero: 'Fútbol', degradado: 'from-lime-500 to-green-700', sigla: 'FC' },
    { valor: 'Apex Legends', nombre: 'Apex Legends', slug: 'apex-legends', genero: 'Battle royale de héroes', degradado: 'from-rose-500 to-red-800', sigla: 'AP' },
    { valor: 'CS2', nombre: 'Counter-Strike 2', slug: 'cs2', genero: 'Shooter táctico 5v5', degradado: 'from-yellow-500 to-amber-700', sigla: 'CS2' },
    { valor: 'Rocket League', nombre: 'Rocket League', slug: 'rocket-league', genero: 'Fútbol con coches', degradado: 'from-cyan-500 to-blue-700', sigla: 'RL' },
    { valor: 'Roblox', nombre: 'Roblox', slug: 'roblox', genero: 'Experiencias multijugador', degradado: 'from-pink-500 to-fuchsia-700', sigla: 'RB' },
    { valor: 'Brawl Stars', nombre: 'Brawl Stars', slug: 'brawl-stars', genero: 'Acción 3v3 en móvil', degradado: 'from-amber-400 to-yellow-600', sigla: 'BS' }
];

export function juegoPorValor(valor) {
    return JUEGOS.find((j) => j.valor === valor) || null;
}

// ---------- 6. Perfiles ----------
// Avatares que cada jugador puede elegir en su perfil (deben coincidir con
// la lista de firestore.rules).
export const AVATARES = ['🎮', '🕹️', '👾', '🎯', '🏆', '⚔️', '🛡️', '🔥', '⚡', '🐉', '🦊', '🐺', '🤖', '👑', '🚀', '💎'];

// IDs de juego que se pueden mostrar en el perfil (clave en Firestore → etiqueta)
export const PLATAFORMAS = [
    { clave: 'riot', etiqueta: 'Riot ID', ejemplo: 'Nombre#TAG' },
    { clave: 'epic', etiqueta: 'Epic Games', ejemplo: 'Tu nombre en Epic' },
    { clave: 'psn', etiqueta: 'PlayStation', ejemplo: 'ID online de PSN' },
    { clave: 'xbox', etiqueta: 'Xbox', ejemplo: 'Gamertag de Xbox' },
    { clave: 'steam', etiqueta: 'Steam', ejemplo: 'Nombre en Steam' },
    { clave: 'nintendo', etiqueta: 'Nintendo', ejemplo: 'SW-0000-0000-0000' },
    { clave: 'activision', etiqueta: 'Activision', ejemplo: 'Nombre#1234567' }
];

export const MAX_JUEGOS_FAVORITOS = 5;

// ============================================================
// Utilidades (no hace falta tocar nada de aquí hacia abajo)
// ============================================================

// Valida la invitación: solo enlaces reales de Discord.
export function enlaceDiscord() {
    try {
        const u = new URL(DISCORD_INVITE);
        const valido = u.protocol === 'https:' &&
            (u.hostname === 'discord.gg' || ((u.hostname === 'discord.com' || u.hostname === 'www.discord.com') && u.pathname.startsWith('/invite/')));
        return valido ? u.href : null;
    } catch {
        return null;
    }
}

export function enlaceTwitch(canal) {
    const limpio = String(canal || '').trim().toLowerCase();
    return /^[a-z0-9_]{3,25}$/.test(limpio) ? `https://www.twitch.tv/${limpio}` : null;
}

// Diferencia en minutos entre la zona horaria de la agenda y UTC en un instante dado
function desfaseMinutos(fecha, zona) {
    const partes = new Intl.DateTimeFormat('en-US', {
        timeZone: zona, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
    }).formatToParts(fecha).reduce((a, p) => (a[p.type] = p.value, a), {});
    const comoUtc = Date.UTC(+partes.year, +partes.month - 1, +partes.day, +partes.hour, +partes.minute);
    return Math.round((comoUtc - fecha.getTime()) / 60000);
}

/**
 * Próxima vez que ocurre un evento semanal, como Date (instante real).
 * Si está ocurriendo ahora (dentro de las 2 h siguientes al inicio), devuelve
 * el inicio de hoy para poder mostrar "¡Ahora!".
 */
export function proximaOcurrencia(evento, ahora = new Date()) {
    const [h, m] = String(evento.hora || '00:00').split(':').map((n) => parseInt(n, 10) || 0);
    for (let i = -1; i <= 7; i++) {
        const base = new Date(ahora.getTime() + i * 86400000);
        // Día de la semana y fecha "locales" en la zona de la agenda
        const local = new Date(base.getTime() + desfaseMinutos(base, ZONA_HORARIA_AGENDA) * 60000);
        if (local.getUTCDay() !== evento.dia) continue;
        const inicioComoUtc = Date.UTC(local.getUTCFullYear(), local.getUTCMonth(), local.getUTCDate(), h, m);
        const inicio = new Date(inicioComoUtc - desfaseMinutos(new Date(inicioComoUtc), ZONA_HORARIA_AGENDA) * 60000);
        if (inicio.getTime() + 2 * 3600000 > ahora.getTime()) return inicio;
    }
    return null;
}
