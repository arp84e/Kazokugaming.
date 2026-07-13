import os
import json
import time
import re
import urllib.parse
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: ESTRATEGA DE GUÍAS TÁCTICAS (MODO RESILIENTE) ===")

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

# --- NUEVO: SISTEMA DE REINTENTOS PARA EVITAR EL ERROR 503 ---
def generar_con_reintentos(prompt_texto, config_ia, max_intentos=5):
    for intento in range(max_intentos):
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt_texto,
                config=config_ia
            )
            return response
        except Exception as e:
            error_str = str(e).lower()
            # Si el error es por saturación (503) o límite (429)
            if "503" in error_str or "unavailable" in error_str or "429" in error_str or "quota" in error_str:
                espera = (intento + 1) * 20  # Esperará 20s, 40s, 60s...
                print(f"⚠️ Servidores de IA saturados. Reintentando en {espera} segundos... (Intento {intento+1}/{max_intentos})")
                time.sleep(espera)
            else:
                raise e # Si es otro tipo de error grave, que se detenga
    raise Exception("❌ Se superó el límite máximo de reintentos. Los servidores están caídos.")

# Cargar base de datos actual para evitar duplicados
datos_web = {"guias": []}
nombres_existentes = []
if os.path.exists(archivo_guias):
    with open(archivo_guias, "r", encoding="utf-8") as f:
        try: 
            datos_web = json.load(f)
            nombres_existentes = [g.get("juego", "").lower() for g in datos_web.get("guias", [])]
        except: pass

entrada_usuario = os.environ.get("INPUT_JUEGO", "").strip()
juegos_a_procesar = []

if entrada_usuario:
    print("🛠️ MODO MANUAL DETECTADO.")
    juegos_a_procesar = [entrada_usuario]
else:
    print("🌍 MODO PILOTO AUTOMÁTICO: Buscando tendencias en la web...")
    prompt_tendencias = f"""
    Eres un analista de datos de la industria de los videojuegos.
    Busca en internet cuáles son los 3 videojuegos más buscados, jugados o populares de esta semana.
    EXCLUYE OBLIGATORIAMENTE los siguientes juegos, ya que ya los tenemos: {nombres_existentes}.
    Devuelve ÚNICAMENTE un JSON con esta estructura exacta, añadiendo el año de lanzamiento para mayor precisión:
    {{
      "juegos": ["Nombre Juego 1 : Año", "Nombre Juego 2 : Año", "Nombre Juego 3 : Año"]
    }}
    """
    try:
        config_tendencias = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.7, tools=[{"google_search": {}}])
        res_tendencias = generar_con_reintentos(prompt_tendencias, config_tendencias)
        data_tendencias = json.loads(extraer_json_seguro(res_tendencias.text))
        juegos_a_procesar = data_tendencias.get("juegos", [])
        print(f"📡 Tendencias detectadas: {juegos_a_procesar}")
    except Exception as e:
        print(f"❌ Error al buscar tendencias: {e}")
        exit(1)

if not juegos_a_procesar:
    print("❌ No hay juegos para procesar.")
    exit(1)

# --- CICLO DE REDACCIÓN DE GUÍAS ---
for entrada in juegos_a_procesar:
    año_especifico = ""
    juego_limpio = entrada

    if ":" in entrada:
        partes = entrada.split(":")
        juego_limpio = partes[0].strip()
        año_especifico = partes[1].strip()

    slug = re.sub(r'[^a-z0-9]+', '-', juego_limpio.lower()).strip('-')
    id_guia = f"guia-{slug}"[:50]

    if any(g["id"] == id_guia for g in datos_web["guias"]):
        print(f"⏭️ Saltando '{juego_limpio}': Ya existe en guias.json.")
        continue

    print(f"\n🔍 Redactando guía extensa para: {juego_limpio} ({año_especifico})...")

    filtro_temporal = f"Lanzado específicamente en el año {año_especifico}." if año_especifico else "No confundir con ediciones anteriores."

    prompt_sistema = f"""
    Eres el Estratega Jefe de KazokuGaming. Busca información real en internet y redacta una GUÍA TÁCTICA AVANZADA Y COMPLETA.
    Juego a analizar: "{juego_limpio}". {filtro_temporal}
    Redacta todo desde cero con estilo profesional, oscuro y analítico.

    ESTRUCTURA OBLIGATORIA (MUY EXTENSA, usa <h2> y <h3>):
    1. <h2>Análisis de la Amenaza</h2>: Contexto táctico.
    2. <h2>Mecánicas de Supervivencia</h2>: Sistemas y tips ocultos.
    3. <h2>Arsenal y Mejores Builds</h2>: Equipamiento superior y localizaciones.
    4. <h2>Desglosando Cuellos de Botella</h2>: Estrategias paso a paso para TODOS los jefes principales.
    5. <h2>Coleccionables Críticos</h2>: Solo objetos valiosos reales.
    6. <h2>Archivos Clasificados</h2>: Códigos, cajas fuertes o exploits.

    REGLAS JSON:
    1. ÚNICAMENTE un objeto JSON.
    2. Usa comillas simples para atributos HTML en 'contenido'.
    {{
      "titulo": "Guía Táctica Definitiva: [Nombre Exacto]",
      "meta_descripcion": "Resumen SEO 150 caracteres",
      "tags": ["Guía Completa", "Secretos", "Jefes"],
      "tiempo_lectura": "X min",
      "contenido": "HTML extenso aquí...",
      "seo": {{ "keywords": "palabra1, palabra2" }},
      "open_graph": {{ "og_title": "Título OG", "og_description": "Desc OG", "og_type": "article" }}
    }}
    """

    try:
        termino_busqueda = f"Guia paso a paso armas jefes trucos secretos {juego_limpio} {año_especifico}".strip()
        config_guia = types.GenerateContentConfig(system_instruction=prompt_sistema, response_mime_type="application/json", temperature=0.35, tools=[{"google_search": {}}])
        
        response = generar_con_reintentos(f"Investiga minuciosamente y redacta: {termino_busqueda}", config_guia)
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
        print(f"✅ ¡Guía de {juego_limpio} guardada con éxito!")
        
        with open(archivo_guias, "w", encoding="utf-8") as f:
            json.dump(datos_web, f, ensure_ascii=False, indent=2)
            
        time.sleep(15) 

    except Exception as e:
        print(f"❌ Error al generar la guía de {juego_limpio}: {e}")

print("\n🚀 PROCESO FINALIZADO.")
