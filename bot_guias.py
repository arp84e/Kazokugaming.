import os
import json
import time
import re
import urllib.parse
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: ESTRATEGA DE GUÍAS TÁCTICAS (VERSIÓN EXTENDIDA V3) ===")

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

print(f"\n🔍 Investigando y redactando guía táctica EXTENSA en internet para: {juego_limpio}...")

filtro_temporal = f"Lanzado específicamente en el año {año_especifico}." if año_especifico else "Asegúrate de no confundir este juego con precuelas, secuelas, remakes o ediciones anteriores."

# --- NUEVO PROMPT EXTENDIDO PARA GUÍAS PROFUNDAS ---
prompt_sistema = f"""
Eres el Estratega Jefe de KazokuGaming. Tu misión es buscar información real, exhaustiva y detallada en internet sobre el videojuego indicado y redactar una GUÍA TÁCTICA AVANZADA Y COMPLETA.

🚨 ADVERTENCIA CRÍTICA DE PRECISIÓN HISTÓRICA:
El juego a analizar es: "{juego_limpio}". {filtro_temporal}
Es OBLIGATORIO que verifiques los hechos, mecánicas y la trama para que correspondan exactamente a la edición solicitada. Redacta todo desde cero con tu propio estilo profesional, oscuro, táctico y analítico para evitar copyright.

ESTRUCTURA OBLIGATORIA DE LA GUÍA (DEBE SER MUY EXTENSA):
No escatimes en palabras. Desarrolla un HTML largo y rico en detalles, estructurado en las siguientes secciones usando etiquetas <h2> y <h3>:

1. <h2>Análisis de la Amenaza (Introducción Táctica)</h2>: Contexto del juego, qué espera al jugador y la mentalidad necesaria para sobrevivir o dominar el juego.
2. <h2>Mecánicas de Supervivencia y Combate</h2>: Explicación profunda de los sistemas del juego (parrys, esquivas, economía, gestión de recursos, cordura, estamina, etc.) y tips ocultos que el tutorial no enseña.
3. <h2>Arsenal y Mejores Builds</h2>: Cuáles son las mejores armas, habilidades o equipamientos del juego, dónde encontrarlas y por qué son tácticamente superiores.
4. <h2>Desglosando los Cuellos de Botella (Jefes y Puzles)</h2>: Estrategias detalladas paso a paso para TODOS los jefes principales o los niveles/puzles más infames. Explica sus fases, patrones de ataque y vulnerabilidades.
5. <h2>Coleccionables Críticos y Mejoras de Inventario</h2>: Ubicaciones exactas de los objetos que realmente cambian la partida (ampliaciones de inventario, fragmentos de salud máxima, armas secretas). Ignora los coleccionables basura (como notas sin valor).
6. <h2>Archivos Clasificados (Trucos, Códigos y Exploits)</h2>: Todas las contraseñas de cajas fuertes, candados, puertas, o atajos mecánicos reales del juego.

REGLAS JSON (ESTRICTAS):
1. ÚNICAMENTE un objeto JSON bien formateado.
2. Usa comillas simples para atributos HTML en la variable 'contenido'.
3. 'contenido': HTML estructurado MUY EXTENSO, limpio y profesional. (Usa <h2>, <h3>, <ul>, <p>, <strong>).

ESTRUCTURA JSON:
{{
  "titulo": "Guía Táctica Definitiva: [Nombre Exacto]",
  "meta_descripcion": "La guía táctica más completa: jefes, builds, coleccionables críticos y códigos para dominar el juego.",
  "tags": ["Guía Completa", "Estrategia", "Secretos", "Jefes"],
  "tiempo_lectura": "X min",
  "contenido": "HTML extenso aquí...",
  "seo": {{ "keywords": "palabra1, palabra2, guia, trucos, walkthrough" }},
  "open_graph": {{
    "og_title": "Guía Definitiva de [Nombre Exacto]",
    "og_description": "Supera las secciones más complejas con nuestro dossier táctico.",
    "og_type": "article"
  }}
}}
"""

try:
    termino_busqueda = f"Guia completa paso a paso armas jefes trucos {juego_limpio} {año_especifico}".strip()
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=f"Investiga minuciosamente en la web y redacta el dossier extenso para: {termino_busqueda}",
        config=types.GenerateContentConfig(
            system_instruction=prompt_sistema, 
            response_mime_type="application/json", 
            temperature=0.35,
            tools=[{"google_search": {}}]
        )
    )
    
    guia_generada = json.loads(extraer_json_seguro(response.text))
    
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
        "tiempo_lectura": guia_generada.get("tiempo_lectura", "10 min"),
        "contenido": guia_generada["contenido"],
        "meta_descripcion": guia_generada["meta_descripcion"],
        "seo": guia_generada.get("seo", {"keywords": f"guia completa {juego_limpio}, trucos, secretos, jefes"}),
        "open_graph": guia_generada.get("open_graph", {"og_title": guia_generada["titulo"], "og_description": guia_generada["meta_descripcion"], "og_type": "article"})
    }
    
    datos_web["guias"].insert(0, guia_final)
    print(f"✅ ¡Guía extensa de {juego_limpio} generada y guardada con éxito en guias.json!")

except Exception as e:
    print(f"❌ Error al generar la guía: {e}")

with open(archivo_guias, "w", encoding="utf-8") as f:
    json.dump(datos_web, f, ensure_ascii=False, indent=2)

print("\n🚀 PROCESO FINALIZADO.")
