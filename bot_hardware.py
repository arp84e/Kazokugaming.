import os
import sys
import json
import time
import re
from google import genai
from google.genai import types
from duckduckgo_search import DDGS

print("=== INICIANDO KAZOKUBOT: ANALISTA DE HARDWARE ===")

# 1. Recibir las variables del formulario de GitHub
nombre_dispositivo = os.environ.get("INPUT_NOMBRE")
categoria = os.environ.get("INPUT_CATEGORIA", "accessory")
analisis_previo = os.environ.get("INPUT_ANALISIS", "")
pros_contras_previos = os.environ.get("INPUT_PROS_CONTRAS", "")
api_key = os.environ.get("GEMINI_API_KEY")

if not nombre_dispositivo:
    print("❌ ERROR: El nombre del dispositivo está vacío.")
    sys.exit(1)
if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    sys.exit(1)

# 2. Configurar la IA
client = genai.Client(api_key=api_key)
seguridad_permisiva = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

# 3. Función para buscar imágenes libres de copyright con DuckDuckGo
def buscar_imagen(query):
    print(f"🔍 Buscando imagen libre para: {query}")
    try:
        resultados = DDGS().images(keywords=f"{query} gaming hardware official", max_results=1)
        for r in resultados:
            print("✅ Imagen encontrada.")
            return r.get("image")
    except Exception as e:
        print(f"⚠️ Aviso: No se pudo buscar la imagen. ({e})")
    
    # Imagen por defecto si falla
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=2070&auto=format&fit=crop"

imagen_url = buscar_imagen(nombre_dispositivo)

# 4. Generar el prompt maestro para el Analista IA
print(f"🧠 Enviando a Gemini para redactar análisis de: {nombre_dispositivo}")
prompt = f"""
Actúa como un experto analista de hardware gaming de la revista KazokuGaming. 
Vas a redactar una reseña técnica profunda, profesional y con tono de 'gaming moderno' para el siguiente dispositivo:
- Nombre: {nombre_dispositivo}
- Categoría: {categoria}

El usuario ha proporcionado estos apuntes en borrador. Debes mejorarlos, corregirlos y ampliarlos con tus conocimientos. Si están vacíos, investiga y genéralos tú mismo:
- Apuntes del usuario: "{analisis_previo}"
- Pros y Contras del usuario: "{pros_contras_previos}"

Devuelve EXCLUSIVAMENTE un objeto JSON válido con la siguiente estructura exacta (sin texto extra, sin markdown de ```json):
{{
  "title": "Nombre Oficial y Completo",
  "brand": "Marca (ej. Razer, Logitech, ASUS)",
  "category": "{categoria}",
  "tier": "media", // IMPORTANTE: Solo si es laptop pon "baja", "media" o "alta". Si es accessory, console o handheld, pon ""
  "desc": "Análisis detallado, apasionante y muy profesional (al menos dos o tres frases potentes).",
  "specs": [
    {{ "label": "Característica 1 (ej. Sensor/Procesador)", "value": "Valor" }},
    {{ "label": "Característica 2 (ej. Peso/Pantalla)", "value": "Valor" }}
  ],
  "pros": ["Pro 1 detallado", "Pro 2", "Pro 3"],
  "contras": ["Contra 1", "Contra 2"],
  "imagen": "{imagen_url}"
}}
"""

try:
    # Usamos Gemini 3.5 Flash por su rapidez y capacidad estructurada
    response = client.models.generate_content(
        model="gemini-3.5-flash", 
        contents=prompt,
        config=types.GenerateContentConfig(
            safety_settings=seguridad_permisiva, 
            response_mime_type="application/json"
        )
    )
    
    nuevo_equipo = json.loads(response.text)
    
    # Asegurar que la imagen se guarde en caso de que la IA la omita
    if "imagen" not in nuevo_equipo or not nuevo_equipo["imagen"]:
         nuevo_equipo["imagen"] = imagen_url
         
except Exception as e:
    print(f"❌ ERROR CATASTRÓFICO CON LA IA: {e}")
    sys.exit(1)

# 5. Guardar en el archivo hardware.json
archivo_json = "hardware.json"

# Crear un "slug" para el ID (Ej: "Logitech G Pro X" -> "logitech-g-pro-x")
id_equipo = re.sub(r'[^a-z0-9]+', '-', nombre_dispositivo.lower()).strip('-')

print("💾 Abriendo base de datos de hardware...")
try:
    with open(archivo_json, "r", encoding="utf-8") as f:
        base_datos = json.load(f)
except FileNotFoundError:
    base_datos = {}

# Añadir o actualizar el equipo
base_datos[id_equipo] = nuevo_equipo

# Guardar
with open(archivo_json, "w", encoding="utf-8") as f:
    json.dump(base_datos, f, indent=2, ensure_ascii=False)

print(f"🎉 ¡ÉXITO! {nuevo_equipo['title']} ha sido añadido a la enciclopedia de KazokuGaming.")
