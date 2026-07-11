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
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    exit(1)

client = genai.Client(api_key=api_key)
archivo_guias = "guias.json"

def extraer_json_seguro(texto):
    match = re.search(r'\{.*\}', texto.strip(), re.DOTALL)
    return match.group(0) if match else texto.strip()

# Cargar base de datos de guías
datos_web = {"guias": []}
if os.path.exists(archivo_guias):
    with open(archivo_guias, "r", encoding="utf-8") as f:
        try: datos_web = json.load(f)
        except: pass

juego_input = os.environ.get("INPUT_JUEGO", "").strip()

if not juego_input:
    print("❌ ERROR: Debes introducir el título de un juego.")
    exit(1)

slug = re.sub(r'[^a-z0-9]+', '-', juego_input.lower()).strip('-')
id_guia = f"guia-{slug}"[:50]

if any(g["id"] == id_guia for g in datos_web["guias"]):
    print(f"⏭️ La guía para '{juego_input}' ya existe. Saliendo...")
    exit(0)

print(f"\n🔍 Investigando y redactando guía táctica para: {juego_input}...")

prompt_sistema = """
Eres el Estratega Jefe de KazokuGaming. Tu misión es buscar información en internet sobre el videojuego indicado y redactar una GUÍA TÁCTICA AVANZADA.
REGLA DE ORO: NO copies texto literal de otras webs. Analiza la información y redáctala desde cero con tu propio estilo profesional, oscuro y analítico.

Enfócate ÚNICAMENTE en:
1. Tips y mecánicas ocultas que el juego no explica.
2. Los 3 o 4 puntos/jefes más difíciles (cómo derrotarlos).
3. Ubicación de objetos ocultos o coleccionables más importantes.
4. Códigos, trucos o 'exploits' (si existen).

REGLAS JSON (ESTRICTAS):
1. ÚNICAMENTE un objeto JSON.
2. Usa comillas simples para atributos HTML en el 'contenido'.
3. 'contenido': HTML limpio (usa <h3>, <ul>, <p>, <strong>).

ESTRUCTURA JSON:
{
  "titulo": "Guía Táctica: [Nombre del Juego]",
  "meta_descripcion": "Resumen de 150 caracteres para SEO",
  "tags": ["Guía", "Trucos", "Secretos"],
  "tiempo_lectura": "X min",
  "contenido": "HTML aquí",
  "seo": { "keywords": "palabra1, palabra2" },
  "open_graph": {
    "og_title": "Guía Definitiva de [Nombre]",
    "og_description": "Supera lo más difícil...",
    "og_type": "article"
  }
}
"""

try:
    # Usamos la herramienta de búsqueda de Google para que la IA investigue online
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=f"Investiga y crea la guía de: {juego_input}",
        config=types.GenerateContentConfig(
            system_instruction=prompt_sistema, 
            response_mime_type="application/json", 
            temperature=0.5,
            tools=[{"google_search": {}}] # Activa la búsqueda web
        )
    )
    
    guia_generada = json.loads(extraer_json_seguro(response.text))
    
    # Buscar portada oficial en RAWG
    imagen_final = "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200"
    if rawg_key:
        try:
            r = requests.get(f"https://api.rawg.io/api/games?key={rawg_key}&search={urllib.parse.quote(juego_input)}&page_size=1", timeout=10).json()
            if r.get("results"): imagen_final = r["results"][0].get("background_image", imagen_final)
        except: pass
    
    guia_final = {
        "id": id_guia,
        "juego": juego_input,
        "titulo": guia_generada["titulo"],
        "slug": slug,
        "categoria": "Guía Táctica",
        "tags": guia_generada.get("tags", []),
        "autor": "Kazoku Estratega",
        "imagen": imagen_final,
        "fecha": time.strftime("%d %b, %Y"),
        "tiempo_lectura": guia_generada.get("tiempo_lectura", "5 min"),
        "contenido": guia_generada["contenido"],
        "meta_descripcion": guia_generada["meta_descripcion"],
        "seo": guia_generada.get("seo", {"keywords": f"guia {juego_input}, trucos, secretos"}),
        "open_graph": guia_generada.get("open_graph", {"og_title": guia_generada["titulo"], "og_description": guia_generada["meta_descripcion"], "og_type": "article"})
    }
    
    datos_web["guias"].insert(0, guia_final)
    print(f"✅ ¡Guía de {juego_input} generada y guardada con éxito!")

except Exception as e:
    print(f"❌ Error al generar la guía: {e}")

with open(archivo_guias, "w", encoding="utf-8") as f:
    json.dump(datos_web, f, ensure_ascii=False, indent=2)

print("\n🚀 PROCESO FINALIZADO.")
