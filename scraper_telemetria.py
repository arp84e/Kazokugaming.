import os
import sys
import json
import time
import requests
import re
import urllib.parse
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: TELEMETRÍA (CONSTRUCTOR ESTÁTICO) ===")
api_key = os.environ.get("GEMINI_API_KEY")
juegos_input = os.environ.get("INPUT_JUEGOS", "Cyberpunk 2077")

if not api_key:
    sys.exit("❌ ERROR: No se encontró GEMINI_API_KEY.")

client = genai.Client(api_key=api_key)
archivo_oficial = "telemetria.json"

estructura_final = {"juegos": []}
if os.path.exists(archivo_oficial):
    with open(archivo_oficial, "r", encoding="utf-8") as f:
        try: estructura_final = json.load(f)
        except: pass

for titulo in juegos_input.split(";"):
    titulo = titulo.strip()
    if not titulo: continue
    
    id_juego = re.sub(r'[^a-z0-9]+', '-', titulo.lower()).strip('-')
    
    prompt = f"Analiza técnicamente el juego {titulo}. Devuelve JSON estricto con: sinopsis, motor_grafico, plataformas, calificacion, analisis_detallado (HTML puro con p y strong), requisitos_minimos (lista de strings), requisitos_recomendados (lista de strings)."
    try:
        res = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(res.text)
        
        nuevo_juego = {
            "id": id_juego,
            "titulo": titulo,
            "fecha": time.strftime("%Y-%m-%d"),
            "plataformas": data.get("plataformas", "PC"),
            "calificacion": data.get("calificacion", "8.5"),
            "motor_grafico": data.get("motor_grafico", "Motor Desconocido"),
            "sinopsis": data.get("sinopsis", "Análisis técnico de rendimiento."),
            "analisis_detallado": data.get("analisis_detallado", "<p>Análisis técnico en detalle...</p>"),
            "requisitos": {
                "minimos": data.get("requisitos_minimos", ["Procesador: Intel i5", "Memoria: 8GB RAM", "Gráficos: GTX 1060"]),
                "recomendados": data.get("requisitos_recomendados", ["Procesador: Intel i7", "Memoria: 16GB RAM", "Gráficos: RTX 3060"])
            },
            "imagen": "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800" # Idealmente usar RAWG API aquí
        }
        
        idx = next((i for i, j in enumerate(estructura_final["juegos"]) if j["id"] == id_juego), None)
        if idx is not None:
            estructura_final["juegos"][idx] = nuevo_juego
        else:
            estructura_final["juegos"].append(nuevo_juego)

        # --- PASO 1 y 2: GENERACIÓN HTML ESTÁTICO Y CONEXIÓN CON RADAR ---
        os.makedirs("telemetria", exist_ok=True)
        html_juego_filename = f"telemetria/{id_juego}.html"
        
        req_min = "".join([f'<li class="flex items-start"><span class="text-cyan-500 mr-2 mt-1 font-bold">▸</span><span>{r}</span></li>' for r in nuevo_juego["requisitos"]["minimos"]])
        req_rec = "".join([f'<li class="flex items-start"><span class="text-cyan-500 mr-2 mt-1 font-bold">▸</span><span>{r}</span></li>' for r in nuevo_juego["requisitos"]["recomendados"]])

        plantilla_juego = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo} | Análisis Técnico & Telemetría</title>
    <meta name="description" content="{nuevo_juego["sinopsis"]}">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style> body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0b0f19; }} </style>
</head>
<body class="text-slate-200 min-h-screen flex flex-col justify-between">
    <div id="header-container"></div>
    <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex-grow w-full">
        
        <div class="lg:flex lg:space-x-10 mb-12">
            <div class="lg:w-1/3 mb-8 lg:mb-0">
                <div class="rounded-2xl overflow-hidden shadow-2xl border border-slate-800/80 sticky top-24">
                    <img src="{nuevo_juego["imagen"]}" alt="{titulo}" class="w-full h-auto object-cover aspect-[3/4]">
                </div>
                
                <!-- PASO 2: WIDGET DE RADAR DE OFERTAS DINÁMICO -->
                <div id="radar-widget" class="mt-6 hidden animate-pulse">
                    <div class="bg-gradient-to-r from-slate-900 to-slate-800 border border-amber-500/40 rounded-xl p-5 text-center shadow-[0_0_20px_rgba(245,158,11,0.15)]">
                        <span class="text-[10px] font-black text-amber-500 uppercase tracking-widest mb-2 block bg-amber-500/10 py-1 rounded">Radar Detectó Oferta</span>
                        <p class="text-white font-black text-3xl mb-3" id="radar-price">$0.00</p>
                        <a href="#" id="radar-link" target="_blank" rel="noopener noreferrer" class="block w-full bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 font-extrabold py-3 rounded-xl transition shadow-lg">Ver en Tienda Oficial →</a>
                    </div>
                </div>
            </div>
            
            <div class="lg:w-2/3 flex flex-col justify-center">
                <div class="flex items-start justify-between mb-2">
                    <h1 class="text-4xl sm:text-5xl font-extrabold text-white tracking-tight pr-4">{titulo}</h1>
                    <div class="flex flex-col items-center justify-center w-20 h-20 min-w-[5rem] bg-slate-900 border-2 border-cyan-500/80 rounded-xl shadow-[0_0_20px_rgba(6,182,212,0.3)]">
                        <span class="text-2xl font-black text-white mt-1">{nuevo_juego["calificacion"]}</span>
                    </div>
                </div>
                <p class="text-sm font-bold text-slate-400 tracking-wide uppercase mb-6">{nuevo_juego["plataformas"]} • {nuevo_juego["motor_grafico"]}</p>
                
                <div class="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-8 text-slate-300 leading-relaxed text-lg mb-8 shadow-inner">
                    {nuevo_juego["analisis_detallado"]}
                </div>
                
                <div class="grid md:grid-cols-2 gap-8 mt-4">
                    <div class="bg-slate-950/60 rounded-2xl p-6 border border-slate-800/60">
                        <h3 class="text-lg font-bold text-slate-200 mb-4 border-b border-slate-800 pb-2">Requisitos Mínimos</h3>
                        <ul class="space-y-3 text-sm text-slate-400">{req_min}</ul>
                    </div>
                    <div class="bg-cyan-950/10 rounded-2xl p-6 border border-cyan-900/30 relative overflow-hidden">
                        <div class="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 rounded-full blur-3xl"></div>
                        <h3 class="text-lg font-bold text-cyan-100 mb-4 border-b border-cyan-900/40 pb-2 relative z-10">Requisitos Recomendados</h3>
                        <ul class="space-y-3 text-sm text-slate-300 relative z-10">{req_rec}</ul>
                    </div>
                </div>
            </div>
        </div>
    </main>
    <script src="../header.js"></script>
    <script>
        // BÚSQUEDA DINÁMICA EN EL RADAR (CHEAPSHARK API)
        const gameTitle = "{titulo}";
        fetch('https://www.cheapshark.com/api/1.0/games?title=' + encodeURIComponent(gameTitle) + '&limit=1')
            .then(res => res.json())
            .then(data => {{
                if(data && data.length > 0) {{
                    const game = data[0];
                    document.getElementById('radar-price').innerText = '$' + parseFloat(game.cheapest).toFixed(2);
                    document.getElementById('radar-link').href = 'https://www.cheapshark.com/redirect?dealID=' + game.cheapestDealID;
                    const widget = document.getElementById('radar-widget');
                    widget.classList.remove('hidden');
                    setTimeout(() => widget.classList.remove('animate-pulse'), 2000);
                }}
            }})
            .catch(err => console.log('Sin ofertas en el radar para este título.'));
    </script>
</body>
</html>'''
        with open(html_juego_filename, "w", encoding="utf-8") as jf:
            jf.write(plantilla_juego)
            
    except Exception as e:
        print(f"❌ Error con {titulo}: {e}")

with open(archivo_oficial, "w", encoding="utf-8") as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)
print("✅ Telemetría estática generada correctamente.")
