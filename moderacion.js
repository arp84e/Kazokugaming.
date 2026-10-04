// moderacion.js
// Filtro de contenido para los textos que los miembros publican en el muro.
//
// IMPORTANTE — qué es y qué NO es este filtro:
//   * Es la PRIMERA capa: da respuesta inmediata al escribir y frena la gran
//     mayoría de mensajes problemáticos antes de publicarse.
//   * NO es infalible. Nadie puede garantizar un filtro automático perfecto:
//     siempre habrá formas creativas de escribir algo ofensivo, y también algún
//     falso positivo. Por eso el muro tiene otras tres capas: un respaldo en
//     firestore.rules (que protege incluso si alguien se salta esta página),
//     el botón de reportar, y la bandeja de moderación del administrador.
//   * Como corre en el navegador, alguien técnico puede saltárselo. Eso es
//     justo lo que cubre el respaldo en las reglas de Firestore.
//
// Para ajustar la severidad cambia NIVEL_FILTRO (ver abajo). Para agregar o
// quitar palabras, edita las listas de más abajo (en minúsculas y SIN acentos;
// la ñ sí se conserva).

// 'estricto'  -> además de lo grave, bloquea groserías suaves (mierda, joder, carajo...)
// 'moderado'  -> bloquea solo insultos, odio, contenido sexual, amenazas, etc.
export const NIVEL_FILTRO = 'estricto';

export const MAX_CARACTERES = 280;
const MIN_CARACTERES = 2;

// ============================================================
// NORMALIZACIÓN (para que escribir "p.u.t.a", "pvta", "m13rd4" o
// "𝗽𝘂𝘁𝗮" no sirva para esquivar el filtro)
// ============================================================

// Letras de otros alfabetos que se ven igual que una letra latina
const HOMOGLIFOS = {
    'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x', 'і': 'i', 'ѕ': 's', 'ј': 'j', 'ԁ': 'd', 'һ': 'h',
    'ο': 'o', 'ν': 'v', 'α': 'a', 'ρ': 'p', 'τ': 't', 'υ': 'u', 'ι': 'i', 'κ': 'k', 'ε': 'e', 'η': 'n',
    'к': 'k', 'у': 'y'
};

const LEET = { '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '@': 'a', '$': 's' };

function normalizarBase(texto) {
    let t = String(texto ?? '');
    t = t.replace(/[\u200B-\u200F\u2060\uFEFF\u00AD]/g, '');           // caracteres invisibles
    t = t.toLowerCase();
    t = Array.from(t).map((c) => HOMOGLIFOS[c] ?? c).join('');
    t = t.replace(/ñ/g, '\u0001');                                      // protege la ñ (coño ≠ cono)
    t = t.normalize('NFKD').replace(/[\u0300-\u036f]/g, '');           // quita acentos, y pasa letras "raras" (𝗽, ｐ) a normales
    t = t.replace(/\u0001/g, 'ñ');
    return t;
}

// Convierte "m13rd4" en "mierda" SOLO en palabras que mezclan letras con números/@/$
// (así "1v1", "ps5" o "3 de la tarde" no se tocan en lo que importa).
function desLeet(t) {
    return t.replace(/[a-zñ0-9@$]+/g, (palabra) => {
        if (!/[a-zñ]/.test(palabra) || !/[0-9@$]/.test(palabra)) return palabra;
        return palabra.replace(/[0-9@$]/g, (c) => LEET[c] ?? c);
    });
}

// "puuuuta" -> "puta", "cabrooon" -> "cabron". Las consonantes dobles (nn, ll, rr...) se dejan
// tal cual porque son normales en español (si no, "penne" se volvería "pene").
const colapsar = (palabra) => palabra.replace(/([a-zñ])\1{2,}/g, '$1').replace(/([aeiou])\1/g, '$1');

// Une secuencias de 3+ letras sueltas: "p u t a" / "p.u.t.a" -> "puta"
function unirLetrasSueltas(palabras) {
    const salida = [];
    let corrida = [];
    const vaciar = () => {
        if (corrida.length >= 3) salida.push(corrida.join(''));
        else salida.push(...corrida);
        corrida = [];
    };
    for (const p of palabras) {
        if (p.length === 1) corrida.push(p);
        else { vaciar(); salida.push(p); }
    }
    vaciar();
    return salida;
}

// "p*ta" / "m*erda": probamos reemplazar el asterisco por cada vocal
function expandirComodines(normalizado) {
    const extra = [];
    for (const trozo of normalizado.split(/\s+/)) {
        if (!trozo.includes('*') || !/[a-zñ]/.test(trozo)) continue;
        for (const vocal of ['a', 'e', 'i', 'o', 'u']) {
            const variante = trozo.replace(/\*{1,2}/, vocal).replace(/[^a-zñ]/g, '');
            if (variante) extra.push(variante);
        }
    }
    return extra;
}

// ============================================================
// LISTAS (minúsculas, sin acentos, ñ conservada)
// ============================================================
const formas = (raiz, sufijos) => sufijos.map((s) => raiz + s);

// Groserías fuertes / insultos vulgares (se bloquean siempre)
const GROSERIAS = new Set([
    ...formas('put', ['a', 'o', 'as', 'os', 'ita', 'ito', 'itas', 'itos', 'ear', 'eada']),
    ...formas('hijueput', ['a', 'as']), ...formas('hijoput', ['a', 'as']), ...formas('hijodeput', ['a', 'as']),
    'hdp', 'ptm', 'ctm', 'csm',
    ...formas('cabron', ['', 'a', 'es', 'as']),
    ...formas('pendej', ['o', 'a', 'os', 'as', 'ada', 'adas']),
    'gilipollas', 'gilipolla',
    ...formas('malparid', ['o', 'a', 'os', 'as']),
    ...formas('gonorrea', ['', 's']),
    ...formas('culer', ['o', 'a', 'os', 'as']),
    ...formas('ching', ['a', 'as', 'ar', 'ue', 'ues', 'ada', 'ado', 'adas', 'ados', 'adera', 'aderas']),
    ...formas('mamon', ['', 'a', 'es', 'as']),
    ...formas('cojud', ['o', 'a', 'os', 'as']),
    ...formas('zorr', ['a', 'as']),
    'coño', 'coños'
]);

// Groserías suaves: solo se bloquean en nivel 'estricto'
const GROSERIAS_SUAVES = new Set([
    ...formas('mierd', ['a', 'as']),
    'joder', 'jodete', 'jodido', 'jodida', 'jodidos', 'jodidas', 'jodas', 'joda', 'jodan',
    'carajo', 'carajos',
    'cagada', 'cagadas', 'cagar', 'cagon', 'cagona',
    'cojones', 'huevon', 'huevona', 'weon', 'weona',
    'mamada', 'mamadas',
    'sexo'
]);

// Insultos directos a personas
const INSULTOS = new Set([
    ...formas('idiot', ['a', 'as']),
    ...formas('imbecil', ['', 'es']),
    ...formas('estupid', ['o', 'a', 'os', 'as']),
    ...formas('tarad', ['o', 'a', 'os', 'as']),
    ...formas('subnormal', ['', 'es']),
    ...formas('retrasad', ['o', 'a', 'os', 'as']),
    ...formas('mongolic', ['o', 'a', 'os', 'as']), 'mongolo', 'mongola',
    ...formas('asquer', ['oso', 'osa', 'osos', 'osas'])
]);

// Odio / discriminación (se bloquean siempre)
const ODIO = new Set([
    'sudaca', 'sudacas', 'negrata', 'negratas',
    ...formas('maricon', ['', 'es']),
    ...formas('maric', ['a', 'as']),
    ...formas('jot', ['o', 'os']),
    ...formas('trol', ['o', 'os']),
    ...formas('tortiller', ['a', 'as']),
    ...formas('travel', ['o', 'os']),
    'feminazi', 'feminazis',
    'heil'
]);

// Contenido sexual (se bloquea siempre)
const SEXUAL = new Set([
    'porno', 'pornografia', 'porn', 'pornhub', 'xxx', 'hentai', 'onlyfans',
    'nudes', 'nude', ...formas('desnud', ['o', 'a', 'os', 'as']),
    ...formas('teta', ['', 's']), ...formas('pezon', ['', 'es']),
    ...formas('pene', ['', 's']), ...formas('vagina', ['', 's']),
    ...formas('verga', ['', 's']), ...formas('poll', ['a', 'as']),
    ...formas('cul', ['o', 'os']),
    'anal', 'semen', 'eyacular', 'orgasmo', 'orgasmos', 'erotico', 'erotica',
    ...formas('foll', ['ar', 'ando', 'a', 'ame', 'en', 'ada', 'ado']),
    ...formas('masturb', ['ar', 'arse', 'acion', 'ando', 'andome']),
    ...formas('pajer', ['o', 'a', 'os', 'as']),
    'chupala', 'chupamela', 'mamame', 'mamamela', 'garchar',
    ...formas('prostitut', ['a', 'as', 'o']), 'prostitucion',
    'pedofilo', 'pedofila', 'pedofilia'
]);

// Familias de palabras que se bloquean además de las listas exactas
const SETS_COLAPSADOS = [GROSERIAS, GROSERIAS_SUAVES, INSULTOS, ODIO, SEXUAL].map((s) =>
    new Set([...s].map(colapsar))
);

// ============================================================
// PATRONES (se aplican sobre el texto normalizado, sin acentos)
// ============================================================
const PATRONES_AUTOLESION = [
    /\bme quiero (morir|matar|suicidar|cortar)/,
    /\bquiero (morir|morirme|matarme|suicidarme|desaparecer para siempre)/,
    /\b(voy a|ire a|me voy a) (suicidarme|matarme)/,
    /\bno quiero (vivir|seguir viviendo|estar vivo|estar viva)/,
    /\b(quitarme|quitarle) la vida/,
    /\b(acabar|terminar) con mi vida/,
    /\bcortarme las venas/,
    /\bhacerme da[nñ]o\b/,
    /\bsuicidarme\b/
];

const PATRONES_AMENAZA = [
    /\bte (voy|vamos) a (matar|violar|asesinar|apu[nñ]alar|disparar|reventar|destrozar|golpear|partir|romper|pegar un tiro)/,
    /\bte (mato|violo|asesino|apu[nñ]alo|disparo|reviento|destrozo)\b/,
    /\b(ojala|espero que|quiero que) (te )?(mueras|mueran|te maten|te violen|te pase algo|te atropellen|te secuestren)/,
    /\b(matate|suicidate|muerete|ahorcate|pegate un tiro|cortate las venas)\b/,
    /\b(tirate|lanzate) (de un|del|desde un|desde el) (puente|edificio|balcon|techo)/,
    /\bse donde (vives|vive|estudias|estudia|trabajas|trabaja)\b/,
    /\btu (ip|direccion) es\b/,
    /\b(dox|doxx)(e|ear|eo|eare|ing|eado)\b/,
    /\bvoy a (ir|llegar|aparecer) (a|en) tu (casa|escuela|colegio|trabajo)/
];

const PATRONES_INSULTO_DIRIGIDO = [
    /\b(eres|sos|ere) (un |una |el |la |tan )?(inutil|inutiles|basura|lacra|escoria|parasito|cancer|fracasad[oa]|perdedor|perdedora|asco|patetic[oa])\b/,
    /\b(me das|das) (asco|pena)\b/,
    /\bque asco de (persona|jugador|jugadora|gente)\b/
];

const PATRONES_ODIO = [
    /\b(judios?|negros?|moros?|indios?|gitanos?|chinos?|latinos?|gringos?|musulmanes|migrantes|inmigrantes) (al horno|a las camaras|de mierda|asquerosos|a su pais)\b/,
    /\bhitler (tenia|tiene) razon\b/,
    /\bsieg heil\b/
];

const PATRONES_SPAM = [
    /\b(nitro|robux|v ?bucks?|pavos|skins?|diamantes|gemas|monedas|cuentas?|giftcards?|tarjetas? de regalo) gratis\b/,
    /\bgratis (nitro|robux|v ?bucks?|pavos|skins?|diamantes|gemas|cuentas?)\b/,
    /\b(vendo|compro|cambio|alquilo) (mi |mis |tu |tus )?(cuentas?|skins?|nitro|robux|elo|rangos?|seguidores)\b/,
    /\b(gana|ganar|ganas) dinero (facil|rapido|desde casa|online|en internet)\b/,
    /\binversion(es)? (segura|segurisima|garantizada)\b/,
    /\b(duplica|multiplica|triplica) tu dinero\b/,
    /\bcriptomonedas? (gratis|seguras?|garantizad)/,
    /\b(boosting|elo ?boost)\b/,
    /\b(sigueme|siganme|suscribete|suscribanse) (a|en) mi\b/
];

const PATRONES_CONTACTO = [
    /\b(mi|mis) (whatsapp|wasap|telegram|instagram|insta|snap|snapchat) (es|son)\b/,
    /\b(pasame|pasenme|dame|dime|manda|mandame|enviame) (tu|su|el) (whatsapp|wasap|telegram|instagram|insta|numero|cel|celular|telefono|correo)\b/,
    /\bescribeme al (privado|inbox|dm|md)\b/
];

// Se evalúan sobre el texto ORIGINAL en minúsculas (no el normalizado)
const REGEX_ENLACE = /(https?:|www\.|\b[a-z0-9-]{2,}\.(com|net|org|gg|tv|xyz|link|club|ru|cn|top|info|app|ly)\b|[a-z0-9-]+\.[a-z]{2,6}\/|discord\s*(\.|punto)\s*gg|\bpunto\s*(com|net|org)\b|\bdot\s*com\b)/i;
const REGEX_ENLACE_SIN_ESPACIOS = /(https?:|www\.|discord\.gg)/i;
const REGEX_CORREO = /[a-z0-9._%+-]+@[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}|\b[a-z0-9._-]+\s*(arroba|\(at\)|\[at\])\s*[a-z0-9-]+/i;
const REGEX_TELEFONO = /(\+?\d[\s.\-()]*){9,}/;
const REGEX_RED_SOCIAL = /\b(whatsapp|wasap|telegram|instagram|insta|snapchat|snap)\b\s*[:=@]/i;

// ============================================================
// MENSAJES para el usuario (tono amable, sin revelar la palabra exacta)
// ============================================================
export const MENSAJES = {
    vacio: 'Escribe algo para publicar.',
    corto: 'Escribe un poco más para poder publicar.',
    largo: `El mensaje es demasiado largo (máximo ${MAX_CARACTERES} caracteres).`,
    groseria: 'Tu mensaje tiene lenguaje vulgar u ofensivo. Reescríbelo con respeto para poder publicarlo.',
    insulto: 'Parece que el mensaje insulta o menosprecia a alguien. En KazokuGaming nos tratamos con respeto.',
    odio: 'No se permiten mensajes discriminatorios ni de odio hacia ninguna persona o grupo.',
    sexual: 'El muro es para todo público: no se permite contenido sexual ni sugerente.',
    amenaza: 'No se permiten amenazas ni mensajes de acoso, ni siquiera en broma.',
    enlace: 'Por seguridad no se permiten enlaces en el muro (suelen usarse para estafas y virus).',
    contacto: 'Por seguridad, no compartas teléfonos, correos ni otros datos de contacto en el muro. Usa el chat de tu escuadrón.',
    spam: 'Este mensaje parece publicidad o una posible estafa (cuentas, regalos gratis, dinero fácil).',
    mayusculas: 'Evita escribir todo en MAYÚSCULAS: se interpreta como gritar.',
    repeticion: 'Evita repetir letras o palabras en exceso.',
    autolesion: 'Lamentamos que estés pasando por un momento difícil, y no queremos que lo vivas solo/a. Este mensaje no se publicará en el muro, pero tu bienestar importa mucho más que cualquier partida: habla con alguien de confianza o busca una línea de ayuda emocional en tu país. 💜'
};

const resultadoBloqueado = (categoria) => ({ ok: false, categoria, mensaje: MENSAJES[categoria] });

// ============================================================
// REVISIÓN PRINCIPAL
// ============================================================
/**
 * Revisa un texto antes de publicarlo.
 * @param {string} textoOriginal
 * @returns {{ok: true, texto: string} | {ok: false, categoria: string, mensaje: string}}
 */
export function revisarTexto(textoOriginal) {
    // 1) Limpieza: un solo párrafo, sin espacios repetidos
    const texto = String(textoOriginal ?? '').replace(/\s+/g, ' ').trim();

    if (!texto) return resultadoBloqueado('vacio');
    if (texto.length < MIN_CARACTERES) return resultadoBloqueado('corto');
    if (texto.length > MAX_CARACTERES) return resultadoBloqueado('largo');

    const minusculas = texto.toLowerCase();

    // 2) Normalización y variantes de comparación
    const normalizado = desLeet(normalizarBase(texto));
    const palabras = normalizado.split(/[^a-zñ]+/).filter(Boolean);
    const palabrasUnidas = unirLetrasSueltas(palabras);
    // Candidatas a comparar: las palabras tal cual + variante con v->u ("pvta") + comodines ("p*ta")
    const candidatas = [...new Set([
        ...palabrasUnidas,
        ...palabrasUnidas.map((p) => p.replace(/v/g, 'u')),
        ...expandirComodines(normalizado)
    ])];
    const candidatasColapsadas = candidatas.map(colapsar);
    const textoPlano = normalizado.replace(/[^a-zñ]+/g, ' ').trim();

    const hayPalabra = (conjunto, idx) =>
        candidatas.some((p) => conjunto.has(p)) ||
        candidatasColapsadas.some((p) => SETS_COLAPSADOS[idx].has(p));

    // 3) Autolesión primero: no se publica, pero se responde con cuidado (no como "infracción")
    if (PATRONES_AUTOLESION.some((r) => r.test(textoPlano))) return resultadoBloqueado('autolesion');

    // 4) Amenazas y acoso
    if (PATRONES_AMENAZA.some((r) => r.test(textoPlano))) return resultadoBloqueado('amenaza');

    // 5) Odio / discriminación
    if (hayPalabra(ODIO, 3) || PATRONES_ODIO.some((r) => r.test(textoPlano))) return resultadoBloqueado('odio');

    // 6) Contenido sexual
    if (hayPalabra(SEXUAL, 4)) return resultadoBloqueado('sexual');

    // 7) Insultos y groserías
    if (hayPalabra(INSULTOS, 2) || PATRONES_INSULTO_DIRIGIDO.some((r) => r.test(textoPlano))) return resultadoBloqueado('insulto');
    if (hayPalabra(GROSERIAS, 0)) return resultadoBloqueado('groseria');
    if (NIVEL_FILTRO === 'estricto' && hayPalabra(GROSERIAS_SUAVES, 1)) return resultadoBloqueado('groseria');

    // 8) Enlaces, datos personales y estafas
    if (REGEX_CORREO.test(minusculas) || REGEX_TELEFONO.test(texto) || REGEX_RED_SOCIAL.test(minusculas)) return resultadoBloqueado('contacto');
    if (REGEX_ENLACE.test(minusculas) || REGEX_ENLACE_SIN_ESPACIOS.test(minusculas.replace(/\s+/g, ''))) return resultadoBloqueado('enlace');
    if (PATRONES_CONTACTO.some((r) => r.test(textoPlano))) return resultadoBloqueado('contacto');
    if (PATRONES_SPAM.some((r) => r.test(textoPlano))) return resultadoBloqueado('spam');

    // 9) Estilo: gritos y repeticiones
    const letras = texto.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]/g, '');
    const mayus = texto.replace(/[^A-ZÁÉÍÓÚÜÑ]/g, '');
    if (letras.length >= 12 && mayus.length / letras.length > 0.7) return resultadoBloqueado('mayusculas');

    if (/(.)\1{7,}/.test(texto.replace(/\s/g, ''))) return resultadoBloqueado('repeticion');
    if (/\b(\S+)(\s+\1\b){4,}/i.test(texto)) return resultadoBloqueado('repeticion');
    if (texto.length >= 10 && new Set(texto.replace(/\s/g, '').toLowerCase()).size < 3) return resultadoBloqueado('repeticion');

    return { ok: true, texto };
}
