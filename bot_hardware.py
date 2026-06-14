import os
import sys
import json
import time
import re
from google import genai
from google.genai import types
from duckduckgo_search import DDGS

print("=== INICIANDO KAZOKUBOT: ANALISTA DE HARDWARE PRO ===")

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

client = genai.Client(api_key=api_key)
seguridad_permisiva = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

def buscar_imagen(query):
    print(f"🔍 Buscando imagen libre para: {query}")
    try:
        resultados = DDGS().images(keywords=f"{query} gaming hardware official", max_results=1)
        for r in resultados:
            print("✅ Imagen encontrada.")
            return r.get("image")
    except Exception as e:
        print(f"⚠️ Aviso: No se pudo buscar la imagen. ({e})")
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=2070"

imagen_url = buscar_imagen(nombre_dispositivo)

print(f"🧠 Generando MEGA-ANÁLISIS técnico para: {nombre_dispositivo}")
prompt = f"""
Actúa como el Director Técnico de Laboratorio de KazokuGaming. Tu tarea es redactar una reseña de hardware exhaustiva, rigurosa, llena de datos precisos y con un lenguaje gamer avanzado y profesional.

Dispositivo: {nombre_dispositivo}
Categoría: {categoria}
Borrador aportado: "{analisis_previo}"
Pros/Contras aportados: "{pros_contras_previos}"

Debes expandir la información de forma masiva y devolver estrictamente un objeto JSON estructurado exactamente así:
{{
  "title": "Nombre comercial completo y correcto del modelo",
  "brand": "Marca fabricante",
  "category": "{categoria}",
  "tier": "media", 
  "score": 88, // Una nota numérica justa del 1 al 100 basada en su calidad/precio
  "desc": "Breve introducción comercial impactante de dos líneas.",
  "analysis_design": "Análisis ultra detallado (mínimo 2 párrafos largos) sobre la ergonomía, la calidad de los materiales de construcción, la estética visual, la distribución de puertos y, críticamente, la eficiencia de su arquitectura térmica, disipadores o ventilación.",
  "analysis_performance": "Evaluación técnica profunda (mínimo 2 párrafos largos) de su rendimiento bruto en juego real. Tasas de cuadros por segundo (FPS) esperadas, fidelidad del panel, respuesta de los switches o joysticks, latencias y comportamiento bajo estrés sostenido.",
  "verdict": "Veredicto editorial final donde expliques claramente si vale la pena la inversión y a qué perfil de jugador exacto va dirigido este dispositivo.",
  "specs": [
    {{ "label": "Componente principal", "value": "Detalle técnico exacto" }},
    {{ "label": "Segunda especificación", "value": "Detalle técnico exacto" }},
    {{ "label": "Tercera especificación", "value": "Detalle técnico exacto" }},
    {{ "label": "Cuarta especificación", "value": "Detalle técnico exacto" }},
    {{ "label": "Quinta especificación", "value": "Detalle técnico exacto" }}
  ],
  "pros": ["Punto fuerte 1 bien desarrollado", "Punto fuerte 2 bien desarrollado", "Punto fuerte 3 bien desarrollado"],
  "contras": ["Desventaja técnica 1 bien explicada", "Desventaja técnica 2 bien explicada"],
  "imagen": "{imagen_url}"
}}
"""

try:
    response = client.models.generate_content(
        model="gemini-3.5-flash", 
        contents=prompt,
        config=types.GenerateContentConfig(
            safety_settings=seguridad_permisiva, 
            response_mime_type="application/json"
        )
    )
    nuevo_equipo = json.loads(response.text)
    if "imagen" not in nuevo_equipo or not nuevo_equipo["imagen"]:
         nuevo_equipo["imagen"] = imagen_url
         
except Exception as e:
    print(f"❌ ERROR CON LA IA: {e}")
    sys.exit(1)

archivo_json = "hardware.json"
id_equipo = re.sub(r'[^a-z0-9]+', '-', nombre_dispositivo.lower()).strip('-')

try:
    with open(archivo_json, "r", encoding="utf-8") as f:
        base_datos = json.load(f)
except FileNotFoundError:
    base_datos = {}

base_datos[id_equipo] = nuevo_equipo

with open(archivo_json, "w", encoding="utf-8") as f:
    json.dump(base_datos, f, indent=2, ensure_ascii=False)

print(f"🎉 ¡ÉXITO! Enciclopedia actualizada.")
