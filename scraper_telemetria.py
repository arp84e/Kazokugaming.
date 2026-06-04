import os
import sys
import json
import time
import requests
import urllib.parse
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: TELEMETRÍA (CON INVESTIGACIÓN WEB) ===")

# Configuración de APIs
api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")

if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

seguridad_permisiva = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

def buscar_portada(titulo):
    """Busca la imagen oficial en la base de datos de RAWG."""
    if not rawg_key: return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    try:
        url = f"https://api.rawg.io/api/games?key={rawg_key}&search={titulo}&page_size=1"
        res = requests.get(url).json()
        if res.get('results'):
            return res['results'][0]['background_image']
    except:
        pass
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"

def buscar_info_extra(titulo):
    """Investiga en Wikipedia en tiempo real para darle contexto exacto a la IA."""
    try:
        query = urllib.parse.quote(titulo + " videojuego")
        url_search = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&utf8=&format=json"
        res_search = requests.get(url_search).json()
        
        if res_search['query']['search']:
            page_title = res_search['query']['search'][0]['title']
            url_summary = f"https://es.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(page_title)}"
            res_summary = requests.get(url_summary).json()
            return res_summary.get('extract', 'No se pudo extraer el texto.')
    except Exception as e:
        pass
    return "Utiliza tu base de datos interna de Wikijuegos y Fandom para obtener la precisión técnica."

nuevos_juegos_raw = os.environ.get("NUEVOS_JUEGOS", "")
sobrescribir = os.environ.get("SOBRESCRIBIR", "false").lower() == "true"
titulos = [linea.strip() for linea in nuevos_juegos_raw.split('\n') if linea.strip()]

if not titulos:
    print("⚠️ No hay títulos para analizar.")
    sys.exit(0)

estructura_final = {"juegos": []}
archivo_json = 'telemetria.json'

if not sobrescribir and os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            estructura_final = json.load(f)
    except:
        pass

for titulo in titulos:
    id_juego = titulo.lower().replace(":", "").replace(" ", "-").replace("/", "-")
    print(f"\n⚙️ Investigando y Analizando: {titulo}...")
    
    # 1. Obtenemos imagen y datos de enciclopedias web
    imagen_real = buscar_portada(titulo)
    contexto_web = buscar_info_extra(titulo)
    print(f"   [+] Datos web extraídos. Redactando expediente...")
    
    # 2. Le pasamos todo a la IA para que lo estructure
    prompt = f"""
    Actúa como experto en hardware y rendimiento (estilo Digital Foundry). Analiza el juego '{titulo}'.
    
    A continuación, tienes información extraída de Wikipedia para asegurar máxima precisión:
    "{contexto_web}"
    
    Combina esta información web con tu conocimiento de Wikijuegos y bases de datos técnicas.
    Devuelve UNICAMENTE un JSON válido con esta estructura:
    {{
        "fecha": "Fecha de lanzamiento exacta",
        "plataformas": "Plataformas de salida",
        "calificacion": "Nota numérica del 1 al 10 en base a críticas",
        "motor_grafico": "Motor (Ej. Unreal Engine 5, RE Engine)",
        "tecnologias": "Tecnologías (DLSS, Ray Tracing, Lumen, etc)",
        "rendimiento": "Resolución y FPS objetivo recomendados",
        "sinopsis": "Sinopsis enciclopédica breve",
        "analisis_detallado": "<p>Escribe 2 párrafos técnicos en HTML analizando los gráficos, físicas y rendimiento en base a la información real.</p>",
        "requisitos": {{
            "minimos": ["..."],
            "recomendados": ["..."]
        }}
    }}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(safety_settings=seguridad_permisiva, response_mime_type="application/json")
        )
        data = json.loads(response.text)
        
        nuevo_juego = {
            "id": id_juego,
            "titulo": titulo,
            "fecha": data.get("fecha", "Por determinar"),
            "plataformas": data.get("plataformas", "Multiplataforma"),
            "calificacion": data.get("calificacion", "N/A"),
            "motor_grafico": data.get("motor_grafico", "No especificado"),
            "tecnologias": data.get("tecnologias", "Estándar"),
            "rendimiento": data.get("rendimiento", "Variable"),
            "sinopsis": data.get("sinopsis", ""),
            "analisis_detallado": data.get("analisis_detallado", "<p>Análisis en proceso...</p>"),
            "requisitos": data.get("requisitos", {"minimos": [], "recomendados": []}),
            "imagen": imagen_real
        }
        
        idx = next((i for i, j in enumerate(estructura_final["juegos"]) if j["id"] == id_juego), None)
        if idx is not None: 
            estructura_final["juegos"][idx] = nuevo_juego
        else: 
            estructura_final["juegos"].append(nuevo_juego)
        
        print("   ✅ Expediente completado.")
        
    except Exception as e:
        print(f"❌ Error redactando {titulo}: {e}")
        # En caso de fallo crítico, guardamos una tarjeta de aviso
        error_juego = {
            "id": id_juego,
            "titulo": f"⚠️ {titulo}",
            "fecha": "ERROR",
            "plataformas": "N/A",
            "calificacion": "0.0",
            "motor_grafico": "N/A",
            "tecnologias": "N/A",
            "rendimiento": "N/A",
            "sinopsis": "Error en la investigación de datos.",
            "analisis_detallado": f"<p class='text-red-400'>Error técnico: {str(e).replace('\"', \"'\")}</p>",
            "requisitos": {"minimos": ["N/A"], "recomendados": ["N/A"]},
            "imagen": imagen_real
        }
        idx = next((i for i, j in enumerate(estructura_final["juegos"]) if j["id"] == id_juego), None)
        if idx is not None: estructura_final["juegos"][idx] = error_juego
        else: estructura_final["juegos"].append(error_juego)
    
    time.sleep(12) # Pausa estratégica para procesar múltiples títulos

with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print("✅ Todos los expedientes han sido guardados con precisión enciclopédica.")
