import os
import sys
import json
import time
import re
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: TELEMETRÍA AVANZADA (DATOS ENRIQUECIDOS) ===")
api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")
juegos_input = os.environ.get("INPUT_JUEGOS", "")
sobrescribir = os.environ.get("SOBRESCRIBIR", "false").lower() == "true"

if not juegos_input:
    print("❌ ERROR: El campo de juegos está vacío.")
    sys.exit(1)
if not api_key:
    sys.exit("❌ ERROR: No se encontró GEMINI_API_KEY.")

client = genai.Client(api_key=api_key)
archivo_oficial = "telemetria.json"

estructura_final = {"juegos": []}
if os.path.exists(archivo_oficial) and not sobrescribir:
    with open(archivo_oficial, "r", encoding="utf-8") as f:
        try: estructura_final = json.load(f)
        except: pass

def buscar_portada(titulo):
    if not rawg_key: return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    try:
        url = f"https://api.rawg.io/api/games?key={rawg_key}&search={requests.utils.quote(titulo)}&page_size=1"
        r = requests.get(url, timeout=10).json()
        if r.get("results"):
            return r["results"][0].get("background_image") or "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    except: pass
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"

for titulo in juegos_input.split(";"):
    titulo = titulo.strip()
    if not titulo: continue
    
    id_juego = re.sub(r'[^a-z0-9]+', '-', titulo.lower()).strip('-')
    imagen_real = buscar_portada(titulo)
    
    prompt = f"Analiza en profundidad el rendimiento técnico de {titulo} en PC. Devuelve únicamente un JSON estricto con: sinopsis (máximo 2 líneas), motor_grafico, plataformas, calificacion (de 1.0 a 10), analisis_detallado (HTML limpio usando <p> y <strong>), requisitos_minimos (lista de 4 strings de componentes), requisitos_recomendados (lista de 4 strings de componentes)."
    
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
            "fecha": time.strftime("%d %b, %Y"),
            "plataformas": data.get("plataformas", "PC"),
            "calificacion": data.get("calificacion", "8.0"),
            "motor_grafico": data.get("motor_grafico", "Custom Engine"),
            "sinopsis": data.get("sinopsis", "Análisis técnico de telemetría y rendimiento in-game."),
            "analisis_detallado": data.get("analisis_detallado", "<p>Procesando datos técnicos...</p>"),
            "requisitos": {
                "minimos": data.get("requisitos_minimos", ["Intel i5", "8GB RAM", "GTX 1060"]),
                "recomendados": data.get("requisitos_recomendados", ["Intel i7", "16GB RAM", "RTX 3060"])
            },
            "imagen": imagen_real
        }
        
        idx = next((i for i, j in enumerate(estructura_final["juegos"]) if j["id"] == id_juego), None)
        if idx is not None:
            estructura_final["juegos"][idx] = nuevo_juego
        else:
            estructura_final["juegos"].append(nuevo_juego)

        # --- GENERACIÓN HTML ESTÁTICO + RADAR + DATOS ESTRUCTURADOS CON ESTRELLAS ---
        os.makedirs("telemetria", exist_ok=True)
        html_juego_filename = f"telemetria/{id_juego}.html"
        
        req_min = "".join([f'<li class="flex items-start text-slate-400"><span class="text-cyan-500 mr-2 mt-1 font-bold">▸</span><span>{r}</span></li>' for r in nuevo_juego["requisitos"]["minimos"]])
        req_rec = "".join([f'<li class="flex items-start text-slate-200"><span class="text-cyan-500 mr-2 mt-1 font-bold">▸</span><span>{r}</span></li>' for r in nuevo_juego["requisitos"]["recomendados"]])

        plantilla_juego = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo} | Análisis Técnico & Telemetría</title>
    <meta name="description" content="{nuevo_juego["sinopsis"]}">
    <link rel="icon" type="image/png" href="../favicon.png">
    
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Game",
      "name": "{titulo}",
      "description": "{nuevo_juego["sinopsis"]}",
      "image": "{nuevo_juego["imagen"]}",
      "author": {{
        "@type": "Organization",
        "name": "KazokuGaming"
      }},
      "review": {{
        "@type": "Review",
        "author": {{
          "@type": "Person",
          "name": "KazokuBot"
        }},
        "reviewRating": {{
          "@type": "Rating",
          "ratingValue": "{nuevo_juego["calificacion"]}",
          "bestRating": "10",
          "worstRating": "1"
        }},
        "reviewBody": "Análisis de rendimiento de telemetría y especificaciones de hardware optimizadas para PC en KazokuGaming."
      }}
    }}
    </script>

    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style> body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0b0f19; }} </style>
</head>
<body class="text-slate-200 min-h-screen flex flex-col justify-between">
    <div id="header-container"></div>
    <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex-grow w-full">
        <div class="lg:flex lg:space-x-10 mb-12">
            <div class="lg:w-1/3 mb-8 lg:mb-0">
                <div class="rounded-2xl overflow-hidden shadow-2xl border border-slate-800 sticky top-24">
                    <img src="{nuevo_juego["imagen"]}" alt="{titulo}" class="w-full h-auto object-cover aspect-[3/4]">
                </div>
                
                <div id="radar-widget" class="mt-6 hidden animate-pulse">
                    <div class="bg-slate-900 border border-amber-500/40 rounded-2xl p-5 text-center shadow-[0_0_25px_rgba(245,158,11,0.15)]">
                        <span class="text-[10px] font-black text-amber-500 uppercase tracking-widest mb-2 block bg-amber-500/10 py-1 rounded">Oferta de Último Minuto</span>
                        <p class="text-white font-black text-3xl mb-3" id="radar-price">$0.00</p>
                        <a href="#" id="radar-link" target="_blank" rel="noopener noreferrer" class="block w-full bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 font-extrabold py-3 rounded-xl transition">Ir a la Oferta →</a>
                    </div>
                </div>
            </div>
            
            <div class="lg:w-2/3 flex flex-col justify-center">
                <div class="flex items-start justify-between mb-4">
                    <h1 class="text-4xl sm:text-5xl font-extrabold text-white tracking-tight pr-4">{titulo}</h1>
                    <div class="flex flex-col items-center justify-center w-20 h-20 min-w-[5rem] bg-slate-900 border-2 border-cyan-500 rounded-2xl shadow-[0_0_20px_rgba(6,182,212,0.25)]">
                        <span class="text-2xl font-black text-white mt-1">{nuevo_juego["calificacion"]}</span>
                    </div>
                </div>
                <p class="text-xs font-bold text-slate-400 tracking-widest uppercase mb-6 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800 inline-block">{nuevo_juego["plataformas"]} • {nuevo_juego["motor_grafico"]}</p>
                
                <div class="bg-slate-900/30 border border-slate-800/60 rounded-3xl p-8 text-slate-300 leading-relaxed text-lg mb-8">
                    {nuevo_juego["analisis_detallado"]}
                </div>
                
                <div class="grid md:grid-cols-2 gap-6">
                    <div class="bg-slate-950/40 rounded-2xl p-6 border border-slate-800/80">
                        <h3 class="font-bold text-slate-200 mb-4 border-b border-slate-800 pb-2 uppercase tracking-wider text-xs">Especificaciones Mínimas</h3>
                        <ul class="space-y-3 text-sm">{req_min}</ul>
                    </div>
                    <div class="bg-cyan-950/10 rounded-2xl p-6 border border-cyan-900/30">
                        <h3 class="font-bold text-cyan-200 mb-4 border-b border-cyan-900/40 pb-2 uppercase tracking-wider text-xs">Especificaciones Recomendadas</h3>
                        <ul class="space-y-3 text-sm">{req_rec}</ul>
                    </div>
                </div>
            </div>
        </div>
    </main>
    <script src="../header.js"></script>
    <script>
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
                    setTimeout(() => widget.classList.remove('animate-pulse'), 1500);
                }}
            }});
    </script>
</body>
</html>'''
        with open(html_juego_filename, "w", encoding="utf-8") as jf:
            jf.write(plantilla_juego)
            
    except Exception as e:
        print(f"❌ Error procesando {titulo}: {e}")

with open(archivo_oficial, "w", encoding="utf-8") as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)
print("✅ Sincronización de telemetría finalizada.")
