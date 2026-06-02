import os
import sys
import json
import time
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: TELEMETRÍA (SISTEMA ANTI-FALLAS) ===")

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

def buscar_portada(titulo_juego):
    if not rawg_key:
        return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    url = f"https://api.rawg.io/api/games?key={rawg_key}&search={titulo_juego}&page_size=1"
    try:
        respuesta = requests.get(url).json()
        if respuesta['results']:
            return respuesta['results'][0]['background_image']
    except Exception as e:
        print(f"⚠️ Error RAWG: {e}")
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"

nuevos_juegos_raw = os.environ.get("NUEVOS_JUEGOS", "")
sobrescribir = os.environ.get("SOBRESCRIBIR", "false").lower() == "true"

titulos = [linea.strip() for linea in nuevos_juegos_raw.split('\n') if linea.strip()]

if not titulos:
    print("⚠️ No hay títulos para analizar. El texto de entrada está vacío.")
    sys.exit(0)

estructura_final = {"juegos": []}
archivo_json = 'telemetria.json'

if not sobrescribir and os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            estructura_final["juegos"] = json.load(f).get("juegos", [])
    except Exception:
        pass

for titulo in titulos:
    print(f"\nProcesando: {titulo}")
    id_juego = titulo.lower().replace(":", "").replace(" ", "-").replace("/", "-")
    indice_existente = next((i for i, j in enumerate(estructura_final["juegos"]) if j["id"] == id_juego), None)
    
    imagen_real = buscar_portada(titulo)
    
    prompt = f"""
    Actúa como un experto analista técnico de videojuegos. Analiza el juego '{titulo}'.
    Devuelve UNICAMENTE un JSON válido con esta estructura exacta:
    {{
        "fecha": "Fecha de lanzamiento",
        "plataformas": "Ej: PC, PS5",
        "calificacion": "Nota numérica del 1 al 10",
        "motor_grafico": "Nombre exacto del motor",
        "tecnologias": "Tecnologías clave",
        "rendimiento": "Resolución y FPS objetivo",
        "sinopsis": "Breve sinopsis general del juego.",
        "analisis_detallado": "<p>Escribe 2 o 3 párrafos en HTML analizando a fondo la arquitectura gráfica.</p>",
        "requisitos": {{
            "minimos": ["..."],
            "recomendados": ["..."]
        }}
    }}
    """
    
    nuevo_expediente = {}
    
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
            "calificacion": datos_ia.get("calificacion", "N/A"),
            "motor_grafico": datos_ia.get("motor_grafico", "No especificado"),
            "tecnologias": datos_ia.get("tecnologias", "Estándar"),
            "rendimiento": datos_ia.get("rendimiento", "Variable"),
            "sinopsis": datos_ia.get("sinopsis", ""),
            "analisis_detallado": datos_ia.get("analisis_detallado", "<p>Análisis en proceso...</p>"),
            "requisitos": datos_ia.get("requisitos", {"minimos": [], "recomendados": []}),
            "imagen": imagen_real
        }
        print("✅ Análisis generado con éxito.")
        
    except Exception as e:
        # ⚠️ AQUÍ ESTÁ EL TRUCO: Si falla, forzamos un expediente de error para que la web lo muestre
        error_msg = str(e).replace('"', "'")
        print(f"⚠️ Error crítico detectado: {error_msg}")
        nuevo_expediente = {
            "id": id_juego,
            "titulo": f"⚠️ Fallo en: {titulo}",
            "fecha": "ERROR",
            "plataformas": "Fallo de Conexión",
            "calificacion": "0.0",
            "motor_grafico": "N/A",
            "tecnologias": "N/A",
            "rendimiento": "N/A",
            "sinopsis": f"El bot encontró un bloqueo al intentar procesar la información. El sistema impidió el análisis.",
            "analisis_detallado": f"<p class='text-red-400 font-bold'>Motivo del error técnico:</p><p class='text-slate-400'>{error_msg}</p>",
            "requisitos": {"minimos": ["Error de red o cuota"], "recomendados": ["Reintentar más tarde"]},
            "imagen": imagen_real
        }
        
    if indice_existente is not None:
        estructura_final["juegos"][indice_existente] = nuevo_expediente
    else:
        estructura_final["juegos"].append(nuevo_expediente)
    
    time.sleep(12)

with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)
print(f"✅ Archivo {archivo_json} guardado con {len(estructura_final['juegos'])} juegos.")
