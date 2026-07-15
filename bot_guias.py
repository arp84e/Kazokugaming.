import os
import json
import time
import re
import urllib.parse
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: ESTRATEGA DE GUÍAS TÁCTICAS ===")

api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")

if not api_key:
    exit("❌ ERROR: No se encontró GEMINI_API_KEY.")

client = genai.Client(api_key=api_key)
archivo_guias = "guias.json"
archivo_juegos = "juegos.json" 

def extraer_json_seguro(texto):
    texto = texto.strip()
    match = re.search(r'\{.*\}', texto, re.DOTALL)
    return match.group(0) if match else texto

def generar_con_reintentos(prompt_texto, config_ia, max_intentos=3):
    modelos_disponibles = ['gemini-3.5-flash', 'gemini-2.5-flash']
    for intento in range(max_intentos):
        for modelo in modelos_disponibles:
            try: return client.models.generate_content(model=modelo, contents=prompt_texto, config=config_ia)
            except Exception as e:
                if "503" in str(e).lower() or "unavailable" in str(e).lower() or "429" in str(e).lower(): continue
                raise e
        time.sleep(10)
    raise Exception("❌ Servidores de IA caídos.")

datos_guias = {"guias": []}
if os.path.exists(archivo_guias):
    with open(archivo_guias, "r", encoding="utf-8") as f:
        try: datos_guias = json.load(f)
        except: pass

datos_juegos = {"juegos": []}
if os.path.exists(archivo_juegos):
    with open(archivo_juegos, "r", encoding="utf-8") as f:
        try: datos_juegos = json.load(f)
        except: pass

juegos_a_procesar = []
titulos_con_guia = [g.get("juego", "").lower() for g in datos_guias.get("guias", [])]
primeros_juegos = datos_juegos.get("juegos", [])[:10]

for j in primeros_juegos:
    titulo = j.get("titulo", "")
    if titulo.lower() not in titulos_con_guia:
        juegos_a_procesar.append(titulo)

if not juegos_a_procesar:
    print("✅ Todos los juegos del TOP 10 actual ya tienen sus guías creadas. No hay trabajo pendiente.")
    exit(0)

print(f"📝 Se detectaron {len(juegos_a_procesar)} juegos del TOP sin guía. Redactando expedientes...")

for juego_limpio in juegos_a_procesar:
    slug = re.sub(r'[^a-z0-9]+', '-', juego_limpio.lower()).strip('-')
    id_guia = f"guia-{slug}"[:50]

    print(f"\n🔍 Redactando dossier para: {juego_limpio}...")

    prompt_sistema = f"""
    Eres el Estratega Jefe de KazokuGaming. Escribe una GUÍA TÁCTICA AVANZADA.
    Juego: "{juego_limpio}".
    Redacta todo con estilo analítico. Devuelve ÚNICAMENTE un objeto JSON válido (sin marcas de formato markdown) con esta estructura:
    {{
      "titulo": "Guía Táctica: [Nombre]",
      "meta_descripcion": "Resumen de 150 caracteres",
      "tags": ["Tag1", "Tag2"],
      "tiempo_lectura": "5 min",
      "contenido": "<h2>Análisis</h2><p>Texto...</p><h2>Mejores Builds o Trucos</h2><p>Texto...</p>",
      "seo": {{ "keywords": "palabra1, palabra2" }},
      "open_graph": {{ "og_title": "Título", "og_description": "Desc", "og_type": "article" }}
    }}
    """

    try:
        termino_busqueda = f"Guia completa trucos secretos mejores armas {juego_limpio}".strip()
        # CORRECCIÓN: Sin response_mime_type
        config_guia = types.GenerateContentConfig(system_instruction=prompt_sistema, temperature=0.35, tools=[{"google_search": {}}])
        
        response = generar_con_reintentos(f"Investiga y redacta la guía de: {termino_busqueda}", config_guia)
        guia_generada = json.loads(extraer_json_seguro(response.text))
        
        imagen_final = "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200"
        if rawg_key:
            try:
                r = requests.get(f"https://api.rawg.io/api/games?key={rawg_key}&search={urllib.parse.quote(juego_limpio)}&page_size=1", timeout=5).json()
                if r.get("results"): imagen_final = r["results"][0].get("background_image", imagen_final)
            except: pass
        
        guia_final = {
            "id": id_guia,
            "juego": juego_limpio,
            "titulo": guia_generada.get("titulo", f"Guía de {juego_limpio}"),
            "slug": slug,
            "categoria": "Guía Táctica",
            "tags": guia_generada.get("tags", []),
            "autor": "Kazoku Estratega",
            "imagen": imagen_final,
            "fecha": time.strftime("%d %b, %Y"),
            "tiempo_lectura": guia_generada.get("tiempo_lectura", "7 min"),
            "contenido": guia_generada.get("contenido", ""),
            "meta_descripcion": guia_generada.get("meta_descripcion", "")
        }
        
        datos_guias["guias"].insert(0, guia_final)
        print(f"✅ ¡Dossier de {juego_limpio} guardado!")
        
        with open(archivo_guias, "w", encoding="utf-8") as f:
            json.dump(datos_guias, f, ensure_ascii=False, indent=2)
            
        time.sleep(5) 

    except Exception as e:
        print(f"❌ Error al procesar {juego_limpio}: {e}")

print("\n🚀 PROCESO DE GUÍAS FINALIZADO.")
