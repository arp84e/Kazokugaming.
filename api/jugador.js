// api/jugador.js - Tu primer servidor Backend en Vercel
export default async function handler(req, res) {
    // 1. Recibimos el nombre del jugador que nos envía tu hub.html
    const nombreJugador = req.query.nombre;

    if (!nombreJugador) {
        return res.status(400).json({ error: "Falta el nombre del jugador." });
    }

    // 2. AQUÍ ESTÁ LA MAGIA SEGURA
    // En el próximo paso, aquí pondremos el código que se conecta a Epic Games y Riot
    // usando nuestras contraseñas secretas (API Keys) que nadie podrá ver.
    // const FORTNITE_API_KEY = process.env.FORTNITE_SECRETO;

    // 3. Por ahora, simulamos que Vercel fue a buscar los datos a los 3 juegos al mismo tiempo
    // y los empaquetamos en un solo formato estándar (JSON) para tu web.
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
            },
            fortnite: {
                victorias: Math.floor(Math.random() * 300),
                bajas: Math.floor(Math.random() * 5000),
                nivel: Math.floor(Math.random() * 200) + 10
            }
        }
    };

    // 4. Se lo enviamos de vuelta a tu hub.html
    res.status(200).json(datosUnificados);
}
