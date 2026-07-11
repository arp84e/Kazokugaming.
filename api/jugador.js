// api/jugador.js - Backend protegido en Vercel
const rateLimit = new Map();

export default async function handler(req, res) {
    // 1. SISTEMA ANTI-DOS (Rate Limiting por IP)
    const ip = req.headers['x-forwarded-for'] || req.socket?.remoteAddress || '127.0.0.1';
    const now = Date.now();
    const windowMs = 60000; // Bloqueo de 1 minuto
    
    if (rateLimit.has(ip)) {
        const requests = rateLimit.get(ip);
        if (requests.count >= 15 && now - requests.startTime < windowMs) {
            return res.status(429).json({ error: "Demasiadas peticiones. Sistema de seguridad activado, espera un minuto." });
        }
        if (now - requests.startTime >= windowMs) {
            rateLimit.set(ip, { count: 1, startTime: now });
        } else {
            requests.count++;
        }
    } else {
        rateLimit.set(ip, { count: 1, startTime: now });
    }

    // 2. LÓGICA DE LA API
    const nombreJugador = req.query.nombre;

    if (!nombreJugador) {
        return res.status(400).json({ error: "Falta el nombre del jugador." });
    }

    // 3. RETORNO DE DATOS SIMULADOS
    const datosUnificados = {
        perfil: {
            nombre: nombreJugador.toUpperCase(),
            nivelGlobal: Math.floor(Math.random() * 500) + 50,
            avatar: "https://images.unsplash.com/photo-1566577739112-5180d4bf9390?q=80&w=200"
        },
        juegos: {
            valorant: {
                rango: "Diamante 2",
                winRate: "54%",
                kd: (Math.random() * (2.0 - 0.8) + 0.8).toFixed(2)
            }
        }
    };

    return res.status(200).json(datosUnificados);
}
