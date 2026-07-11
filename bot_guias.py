import os
import json
import time
import re
import urllib.parse
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: ESTRATEGA DE GUÍAS TÁCTICAS (ANTI-CONFUSIÓN V2) ===")

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

entrada_usuario = os.environ.get("INPUT_JUEGO", "").strip()

if not entrada_usuario:
    print("❌ ERROR: Debes introducir el título de un juego.")
    exit(1)

# --- SISTEMA DE VERIFICACIÓN DE FORMATO Y CONTEXTO ---
# Detecta si el usuario mandó el formato "Juego : Año"
año_especifico = ""
juego_limpio = entrada_usuario

if ":" in entrada_usuario:
    partes = entrada_usuario.split(":")
    juego_limpio = partes[0].strip()
    año_especifico = partes[1].strip()
    print(f"🎯 Formato estricto detectado: Juego = '{juego_limpio}' | Año Restringido = '{año_especifico}'")
else:
    print(f"⚠️ Alerta: Ejecutando sin año específico. Se recomienda usar el formato 'Juego : Año' para evitar homónimos.")

slug = re.sub(r'[^a-z0-9]+', '-', juego_limpio.lower()).strip('-')
id_guia = f"guia-{slug}"[:50]

if any(g["id"] == id_guia for g in datos_web["guias"]):
    print(f"⏭️ La guía para '{juego_limpio}' ya existe en el archivo guias.json. Saliendo...")
    exit(0)

print(f"\n🔍 Investigando y redactando guía táctica en internet para: {juego_limpio}...")

# Modificamos dinámicamente el prompt con restricciones en base a la entrada
filtro_temporal = f"Lanzado específicamente en el año {año_especifico}." if año_especifico else "Asegúrate de no confundir este juego con precuelas, secuelas, remakes o ediciones anteriores del mismo nombre."

prompt_sistema = f"""
Eres el Estratega Jefe de KazokuGaming. Tu misión es buscar información real en internet sobre el videojuego indicado y redactar una GUÍA TÁCTICA AVANZADA.

🚨 ADVERTENCIA CRÍTICA DE PRECISIÓN HISTÓRICA:
El juego a analizar es: "{juego_limpio}". {filtro_temporal}
Es OBLIGATORIO que verifiques los hechos, jefes, personajes y la trama. Si el usuario te pide la secuela (ej. Alan Wake 2), bajo ningún concepto hables de las mecánicas o sucesos de la primera edición (ej. los termos de café o Bright Falls de 2010 exclusivamente). Debes centrarte única y exclusivamente en el contenido de la edición solicitada. Redacta todo desde cero con tu propio estilo profesional, oscuro y analítico para evitar copyright.

Enfócate ÚNICAMENTE en:
1. Tips y mecánicas tácticas avanzadas u ocultas de esta edición.
2. Los 3 o 4 cuellos de botella / puzles / jefes más difíciles de ESTA edición específica y cómo superarlos.
3. Ubicación de objetos ocultos o coleccionables más valiosos.
4. Códigos, combinaciones de cajas fuertes, trucos o 'exploits' reales del juego.

REGLAS JSON (ESTRICTAS):
1. ÚNICAMENTE un objeto JSON bien formateado.
2. Usa comillas simples para atributos HTML en la variable 'contenido'.
3. 'contenido': HTML estructurado limpio (usa <h3>, <ul>, <p>, <strong>).

ESTRUCTURA JSON:
{{
  "titulo": "Guía Táctica: [Nombre Exacto del Juego]",
  "meta_descripcion": "Resumen de 150 caracteres enfocado en el SEO de esta edición",
  "tags": ["Guía", "Trucos", "Secretos"],
  "tiempo_lectura": "X min",
  "contenido": "HTML aquí",
  "seo": {{ "keywords": "palabra1, palabra2" }},
  "open_graph": {{
    "og_title": "Guía Definitiva de [Nombre Exacto]",
    "og_description": "Supera las secciones más complejas de este título...",
    "og_type": "article"
  }}
}}
"""

try:
    # Agregamos el año directamente en el query de búsqueda para forzar a la IA a leer las fuentes correctas
    termino_busqueda = f"Guia completa trucos secretos {juego_limpio} {año_especifico}".strip()
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=f"Investiga en la web de forma rigurosa y genera la guía usando: {termino_busqueda}",
        config=types.GenerateContentConfig(
            system_instruction=prompt_sistema, 
            response_mime_type="application/json", 
            temperature=0.3, # Bajamos la temperatura para evitar alucinaciones y hacerlo hiper-preciso
            tools=[{"google_search": {}}]
        )
    )
    
    guia_generada = json.loads(extraer_json_seguro(response.text))
    
    # Buscar portada oficial en RAWG usando el nombre limpio sin el año de la etiqueta
    imagen_final = "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200"
    if rawg_key:
        try:
            query_rawg = f"{juego_limpio} {año_especifico}".strip()
            r = requests.get(f"https://api.rawg.io/api/games?key={rawg_key}&search={urllib.parse.quote(query_rawg)}&page_size=1", timeout=10).json()
            if r.get("results"): imagen_final = r["results"][0].get("background_image", imagen_final)
        except: pass
    
    guia_final = {
        "id": id_guia,
        "juego": juego_limpio,
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
        "seo": guia_generada.get("seo", {"keywords": f"guia {juego_limpio}, trucos, secretos"}),
        "open_graph": guia_generada.get("open_graph", {"og_title": guia_generada["titulo"], "og_description": guia_generada["meta_descripcion"], "og_type": "article"})
    }
    
    datos_web["guias"].insert(0, guia_final)
    print(f"✅ ¡Guía de {juego_limpio} verificada, generada y guardada con éxito en guias.json!")

except Exception as e:
    print(f"❌ Error al generar la guía: {e}")

with open(archivo_guias, "w", encoding="utf-8") as f:
    json.dump(datos_web, f, ensure_ascii=False, indent=2)

print("\n🚀 PROCESO FINALIZADO.")
