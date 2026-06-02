import os
import sys
import json
import time
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: TELEMETRÍA (VERSIÓN FINAL) ===")

# Configuración de APIs
api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")

if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# Configuración de seguridad para evitar bloqueos
seguridad_permisiva = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

def buscar_portada(titulo):
    """Busca la imagen oficial en RAWG."""
    if not rawg_key: return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    try:
        url = f"https://api.rawg.io/api/games?key={rawg_key}&search={titulo}&page_size=1"
        res = requests.get(url).json()
        if res.get('results'):
            return res['results'][0]['background_image']
    except:
        pass
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"

# Variables de entrada desde GitHub Actions
nuevos_juegos_raw = os.environ.get("NUEVOS_JUEGOS", "")
sobrescribir = os.environ.get("SOBRESCRIBIR", "false").lower() == "true"
titulos = [linea.strip() for linea in nuevos_juegos_raw.split('\n') if linea.strip()]

# Carga inicial del archivo actual
estructura_final = {"juegos": []}
archivo_json = 'telemetria.json'

if not sobrescribir and os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            estructura_final = json.load(f)
    except:
        pass

# Procesamiento de cada juego
for titulo in titulos:
    id_juego = titulo.lower().replace(":", "").replace(" ", "-").replace("/", "-")
    print(f"⚙️ Analizando: {titulo}...")
    
    prompt = f"""
    Actúa como experto en hardware y rendimiento (estilo Digital Foundry). Analiza: '{titulo}'.
    Devuelve UNICAMENTE un JSON válido con esta estructura:
    {{
        "fecha": "Fecha",
        "plataformas": "Plataformas",
        "calificacion": "Nota numérica del 1 al 10",
        "motor_grafico": "Motor",
        "tecnologias": "Tecnologías (DLSS, Ray Tracing...)",
        "rendimiento": "Resolución y FPS objetivo",
        "sinopsis": "Sinopsis breve",
        "analisis_detallado": "<p>Análisis técnico con 2 párrafos.</p>",
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
            "imagen": buscar_portada(titulo)
        }
        
        # Reemplazar o añadir
        idx = next((i for i, j in enumerate(estructura_final["juegos"]) if j["id"] == id_juego), None)
        if idx is not None: estructura_final["juegos"][idx] = nuevo_juego
        else: estructura_final["juegos"].append(nuevo_juego)
        
    except Exception as e:
        print(f"❌ Error en {titulo}: {e}")
    
    time.sleep(15) # Pausa estratégica para la API

# Guardado final
with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print("✅ Expedientes guardados con éxito.")
