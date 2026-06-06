import os
import sys
import json
import time
import requests
import urllib.parse
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: TELEMETRÍA (SISTEMA DE FORMULARIO MULTI-CUADRO) ===")

# Configuración de APIs
api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")

if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# Configuración de seguridad
seguridad_permisiva = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

def buscar_portada(titulo):
    if not rawg_key: return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    try:
        url = f"https://api.rawg.io/api/games?key={rawg_key}&search={titulo}&page_size=1"
        res = requests.get(url).json()
        if res.get('results'):
            return res['results'][0]['background_image']
    except:
        pass
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"

def buscar_info_extra(titulo):
    try:
        query = urllib.parse.quote(titulo + " videojuego")
        url_search = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&utf8=&format=json"
        res_search = requests.get(url_search).json()
        
        if res_search['query']['search']:
            page_title = res_search['query']['search'][0]['title']
            url_summary = f"https://es.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(page_title)}"
            res_summary = requests.get(url_summary).json()
            return res_summary.get('extract', 'Sin datos en Wikipedia.')
    except:
        pass
    return "Utiliza tu base de datos interna para obtener precisión técnica."

# 1. CAPTURA DE DATOS DESDE LOS DIFERENTES CUADROS
juegos_raw = os.environ.get("INPUT_JUEGOS", "")
calificacion_cuadro = os.environ.get("INPUT_CALIFICACION", "").strip()
plataformas_cuadro = os.environ.get("INPUT_PLATAFORMAS", "").strip()
requisitos_cuadro = os.environ.get("INPUT_REQUISITOS", "").strip()
analisis_cuadro = os.environ.get("INPUT_ANALISIS", "").strip()
sobrescribir = os.environ.get("SOBRESCRIBIR", "false").lower() == "true"

# Procesamos la lista de títulos usando punto y coma (;)
texto_unificado = juegos_raw.replace("\n", ";")
titulos = [t.strip() for t in texto_unificado.split(';') if t.strip()]

if not titulos:
    print("⚠️ No se detectó ningún título en la casilla principal.")
    sys.exit(0)

# 2. CARGAR EL ARCHIVO BASE ACTUAL
estructura_final = {"juegos": []}
archivo_json = 'telemetria.json'

if not sobrescribir and os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos_viejos = json.load(f)
            if isinstance(datos_viejos, dict) and "juegos" in datos_viejos:
                estructura_final["juegos"] = datos_viejos["juegos"]
    except:
        pass

# 3. PROCESAR CADA JUEGO EN LA LISTA
for indice, titulo in enumerate(titulos):
    id_juego = titulo.lower().replace(":", "").replace(" ", "-").replace("'", "").replace(".", "")
    imagen_real = buscar_portada(titulo)
    
    # Comprobamos si es el PRIMER JUEGO y si tiene datos manuales rellenados en los cuadros
    es_primer_juego = (indice == 0)
    tiene_datos_manuales = (analisis_cuadro or requisitos_cuadro or calificacion_cuadro or plataformas_cuadro)
    
    if es_primer_juego and tiene_datos_manuales:
        # MODO CUADRO MANUAL (Aplica reescritura anti-copyright para el primer título)
        print(f"\n⚙️ [MODO FORMULARIO MANUAL] Analizando y Reescriturando original: {titulo}...")
        
        prompt = f"""
        Actúas como un redactor técnico senior de videojuegos (estilo Digital Foundry). 
        Se te han provisto notas y análisis manuales para el juego '{titulo}'.
        Tu misión es REESCRIBIR Y READAPTAR COMPLETAMENTE el análisis base para garantizar que sea 100% original, libre de plagio y con un lenguaje periodístico fluido.

        Datos aportados por el usuario:
        - Calificación: {calificacion_cuadro if calificacion_cuadro else 'Calificación web automatizada'}
        - Plataformas sugeridas: {plataformas_cuadro if plataformas_cuadro else 'Buscar estándar'}
        - Requisitos crudos: "{requisitos_cuadro}"
        - Texto de análisis/sinopsis base: "{analisis_cuadro}"

        Instrucciones:
        1. Estructura los requisitos aportados en listas limpias para los campos "minimos" y "recomendados".
        2. El "analisis_detallado" debe constar de 2 párrafos redactados en HTML (<p>...</p>) transformando el texto base de forma elegante y técnica.

        Devuelve UNICAMENTE un JSON válido con esta estructura:
        {{
            "fecha": "Fecha de lanzamiento real o estimada",
            "plataformas": "{plataformas_cuadro if plataformas_cuadro else 'Multiplataforma'}",
            "calificacion": "{calificacion_cuadro if calificacion_cuadro else '8.5'}",
            "motor_grafico": "Motor gráfico utilizado (o 'No especificado')",
            "tecnologias": "Tecnologías clave deducidas (DLSS, FSR, Ray Tracing, etc.)",
            "rendimiento": "Resolución y FPS objetivo recomendados",
            "sinopsis": "Sinopsis de 2 líneas escrita con tus propias palabras.",
            "analisis_detallado": "<p>Primer párrafo reescrito.</p><p>Segundo párrafo técnico reescrito.</p>",
            "requisitos": {{
                "minimos": ["Dato extraído 1", "Dato extraído 2"],
                "recomendados": ["Dato extraído 1", "Dato extraído 2"]
            }}
        }}
        """
    else:
        # MODO AUTOMÁTICO TRADICIONAL (Para el segundo juego en adelante, o si envías todo vacío)
        print(f"\n⚙️ [MODO AUTOMÁTICO INTELIGENTE] Investigando en internet: {titulo}...")
        contexto_web = buscar_info_extra(titulo)
        
        prompt = f"""
        Actúa como experto en hardware y rendimiento. Analiza el juego '{titulo}'.
        Contexto enciclopédico extraído: "{contexto_web}"
        
        Devuelve UNICAMENTE un JSON válido con esta estructura:
        {{
            "fecha": "Fecha de lanzamiento exacta",
            "plataformas": "Plataformas de salida",
            "calificacion": "Nota numérica del 1 al 10 en base a críticas",
            "motor_grafico": "Motor (Ej. Unreal Engine 5)",
            "tecnologias": "Tecnologías (DLSS, Ray Tracing, etc)",
            "rendimiento": "Resolución y FPS objetivo recomendados",
            "sinopsis": "Sinopsis enciclopédica breve",
            "analisis_detallado": "<p>Escribe 2 párrafos técnicos en HTML analizando los gráficos, físicas y rendimiento.</p>",
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
            "imagen": imagen_real
        }
        
        idx = next((i for i, j in enumerate(estructura_final["juegos"]) if j["id"] == id_juego), None)
        if idx is not None: estructura_final["juegos"][idx] = nuevo_juego
        else: estructura_final["juegos"].append(nuevo_juego)
            
        print(f"   ✅ {titulo} completado con éxito.")
        
    except Exception as e:
        print(f"❌ Error procesando {titulo}: {e}")
        error_msg = str(e).replace('"', "'")
        error_juego = {
            "id": id_juego,
            "titulo": f"⚠️ {titulo}",
            "fecha": "ERROR",
            "plataformas": "N/A",
            "calificacion": "0.0",
            "motor_grafico": "N/A",
            "tecnologias": "N/A",
            "rendimiento": "N/A",
            "sinopsis": "Fallo en la sincronización de datos o lectura del formulario.",
            "analisis_detallado": f"<p class='text-red-400'>Error en transformación: {error_msg}</p>",
            "requisitos": {"minimos": ["N/A"], "recomendados": ["N/A"]},
            "imagen": imagen_real
        }
        idx = next((i for i, j in enumerate(estructura_final["juegos"]) if j["id"] == id_juego), None)
        if idx is not None: estructura_final["juegos"][idx] = error_juego
        else: estructura_final["juegos"].append(error_juego)
        
    time.sleep(12)

# 4. APLICAR CAMBIOS EN EL DISCO
with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print("✅ Base de datos telemetria.json actualizada de forma segura.")
