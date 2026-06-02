import os
import sys
import json
import time
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: TELEMETRÍA ===")

api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY") # 👈 Recuperamos tu llave de RAWG

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

# 🛠️ FUNCIÓN PARA OBTENER LA PORTADA REAL
def buscar_portada(titulo_juego):
    if not rawg_key:
        return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=400"
    
    url = f"https://api.rawg.io/api/games?key={rawg_key}&search={titulo_juego}&page_size=1"
    try:
        respuesta = requests.get(url).json()
        if respuesta['results']:
            return respuesta['results'][0]['background_image']
    except Exception as e:
        print(f"⚠️ Error buscando imagen en RAWG: {e}")
    
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=400"

nuevos_juegos_raw = os.environ.get("NUEVOS_JUEGOS", "")
sobrescribir = os.environ.get("SOBRESCRIBIR", "false").lower() == "true"

titulos = [linea.strip() for linea in nuevos_juegos_raw.split('\n') if linea.strip()]

if not titulos:
    print("⚠️ No se proporcionaron juegos para analizar.")
    sys.exit(0)

estructura_final = {"juegos": []}
archivo_json = 'telemetria.json'

if not sobrescribir and os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos_existentes = json.load(f)
            if "juegos" in datos_existentes:
                estructura_final["juegos"] = datos_existentes["juegos"]
    except Exception as e:
        print(f"⚠️ Error al leer JSON antiguo: {e}")

for titulo in titulos:
    print(f"\nProcesando telemetría para: {titulo}")
    id_juego = titulo.lower().replace(":", "").replace(" ", "-").replace("/", "-")
    indice_existente = next((i for i, j in enumerate(estructura_final["juegos"]) if j["id"] == id_juego), None)
    
    # 📸 Buscamos la imagen real primero
    imagen_real = buscar_portada(titulo)
    
    prompt = f"""
    Actúa como un experto en hardware y rendimiento de videojuegos. Analiza: '{titulo}'.
    Devuelve un JSON con este formato exacto:
    {{
        "fecha": "Fecha de lanzamiento",
        "plataformas": "Ej: PC, PS5",
        "sinopsis": "Párrafo técnico sobre el motor gráfico.",
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
        
        datos_ia = json.loads(response.text)
        
        nuevo_expediente = {
            "id": id_juego,
            "titulo": titulo,
            "fecha": datos_ia.get("fecha", "Por determinar"),
            "plataformas": datos_ia.get("plataformas", "Multiplataforma"),
            "sinopsis": datos_ia.get("sinopsis", "Análisis en curso..."),
            "requisitos": datos_ia.get("requisitos", {"minimos": [], "recomendados": []}),
            "imagen": imagen_real # 👈 Inyectamos la imagen descargada de la API
        }
        
        if indice_existente is not None:
            estructura_final["juegos"][indice_existente] = nuevo_expediente
        else:
            estructura_final["juegos"].append(nuevo_expediente)
            
    except Exception as e:
        print(f"⚠️ Error procesando {titulo}: {e}")
    
    time.sleep(12)

with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print("✅ telemetria.json actualizado con imágenes reales.")
