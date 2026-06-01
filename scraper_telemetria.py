import os
import sys
import json
import time
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: TELEMETRÍA (MODO MANUAL) ===")

api_key = os.environ.get("GEMINI_API_KEY")
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

# Recibir variables desde GitHub Actions
nuevos_juegos_raw = os.environ.get("NUEVOS_JUEGOS", "")
sobrescribir = os.environ.get("SOBRESCRIBIR", "false").lower() == "true"

# Limpiar la lista de juegos recibida (uno por línea)
titulos = [linea.strip() for linea in nuevos_juegos_raw.split('\n') if linea.strip()]

if not titulos:
    print("⚠️ No se proporcionaron juegos para analizar. Finalizando script.")
    sys.exit(0)

# Cargar el archivo telemetria.json existente o crear uno nuevo
estructura_final = {"juegos": []}
archivo_json = 'telemetria.json'

# --- LÍNEA CORREGIDA AQUÍ ---
if not sobrescribir and os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos_existentes = json.load(f)
            if "juegos" in datos_existentes:
                estructura_final["juegos"] = datos_existentes["juegos"]
        print(f"✅ Archivo anterior cargado. Manteniendo {len(estructura_final['juegos'])} expedientes existentes.")
    except Exception as e:
        print(f"⚠️ Error al leer el JSON anterior, se creará uno nuevo. Error: {e}")
elif sobrescribir:
    print("⚠️ MODO SOBRESCRIBIR ACTIVADO: Se eliminará el catálogo anterior.")

# Procesar los nuevos juegos
for titulo in titulos:
    print(f"\nProcesando telemetría para: {titulo}")
    id_juego = titulo.lower().replace(":", "").replace(" ", "-").replace("/", "-")
    
    # Comprobar si el juego ya existe en el JSON para actualizarlo en lugar de duplicarlo
    indice_existente = next((i for i, j in enumerate(estructura_final["juegos"]) if j["id"] == id_juego), None)
    
    prompt = f"""
    Actúa como un experto en hardware y rendimiento de videojuegos. Analiza el juego '{titulo}'.
    Devuelve un JSON con el siguiente formato exacto:
    {{
        "fecha": "Fecha de lanzamiento confirmada o 'Por determinar'",
        "plataformas": "Ej: PC, PS5, Xbox Series X/S",
        "sinopsis": "Un párrafo técnico de 4-5 líneas analizando exclusivamente el motor gráfico, físicas y arquitectura técnica.",
        "requisitos": {{
            "minimos": ["Procesador: ...", "Gráficos: ...", "Memoria: ...", "Almacenamiento: ..."],
            "recomendados": ["Procesador: ...", "Gráficos: ...", "Memoria: ...", "Almacenamiento: ..."]
        }},
        "imagen": "Genera una URL de imagen representativa o escribe 'assets/default.jpg'"
    }}
    Responde ÚNICAMENTE con la estructura JSON solicitada.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=seguridad_permisiva,
                response_mime_type="application/json",
            )
        )
        
        datos_ia = json.loads(response.text)
        
        nuevo_expediente = {
            "id": id_juego,
            "titulo": titulo,
            "fecha": datos_ia.get("fecha", "Por determinar"),
            "plataformas": datos_ia.get("plataformas", "Multiplataforma"),
            "sinopsis": datos_ia.get("sinopsis", "Análisis técnico en curso..."),
            "requisitos": datos_ia.get("requisitos", {"minimos": [], "recomendados": []}),
            "imagen": datos_ia.get("imagen", "") 
        }
        
        if indice_existente is not None:
            # Actualiza el existente
            estructura_final["juegos"][indice_existente] = nuevo_expediente
            print(f"🔄 {titulo} actualizado en el catálogo.")
        else:
            # Lo añade al final (append)
            estructura_final["juegos"].append(nuevo_expediente)
            print(f"✅ {titulo} añadido al catálogo.")
            
    except Exception as e:
        print(f"⚠️ Error al procesar {titulo}: {e}")
    
    print("⏳ Esperando 15 segundos para proteger la API de Gemini...")
    time.sleep(15)

# Guardar el resultado fusionado
with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print(f"✅ Proceso terminado. Total de expedientes en telemetria.json: {len(estructura_final['juegos'])}")
