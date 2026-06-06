import os
import sys
import json
import time
import requests
import urllib.parse
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: TELEMETRÍA (MÓDULO ANTI-COPYRIGHT + MANUAL) ===")

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

# 1. RECEPCIÓN Y PARSEO INTELIGENTE DE ENTRADAS
nuevos_juegos_raw = os.environ.get("NUEVOS_JUEGOS", "")
sobrescribir = os.environ.get("SOBRESCRIBIR", "false").lower() == "true"

texto_unificado = nuevos_juegos_raw.replace("\n", ";")
bloques_juegos = [linea.strip() for linea in texto_unificado.split(';') if linea.strip()]

if not bloques_juegos:
    print("⚠️ No se detectaron entradas. Entrada recibida:", nuevos_juegos_raw)
    sys.exit(0)

# 2. CARGAR ARCHIVO ACTUAL
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

# 3. PROCESAR EXPEDIENTES
for bloque in bloques_juegos:
    # Inicializamos variables por defecto
    modo_manual = False
    calificacion_manual = "N/A"
    requisitos_manuales = ""
    analisis_manual = ""
    
    # Comprobamos si el bloque tiene datos manuales divididos por "|"
    if "|" in bloque:
        modo_manual = True
        partes = [p.strip() for p in bloque.split('|')]
        titulo = partes[0]
        
        if len(partes) > 1: calificacion_manual = partes[1]
        if len(partes) > 2: requisitos_manuales = partes[2]
        if len(partes) > 3: analisis_manual = partes[3]
    else:
        titulo = bloque

    id_juego = titulo.lower().replace(":", "").replace(" ", "-").replace("'", "").replace(".", "")
    print(f"\n⚙️ Procesando [{ 'MODO MANUAL ASSIST' if modo_manual else 'MODO AUTOMÁTICO' }]: {titulo}...")
    
    imagen_real = buscar_portada(titulo)
    
    # Construcción del prompt según el modo seleccionado
    if modo_manual:
        print("   [+] Ejecutando filtro anti-plagio y reescritura de estilo para KazokuGaming...")
        prompt = f"""
        Actúas como un redactor técnico senior de videojuegos con un estilo original, analítico y crítico (estilo Digital Foundry).
        Se te ha provisto un análisis crudo y notas de un videojuego que pueden tener problemas de copyright o derechos de autor si se copian directamente.
        Tu misión es REESCRIBIR Y READAPTAR COMPLETAMENTE la información con tus propias palabras, garantizando un texto 100% original, libre de plagio y con lenguaje periodístico avanzado.

        Juego: '{titulo}'
        Nota asignada por el usuario: {calificacion_manual}
        Requisitos en bruto aportados: "{requisitos_manuales}"
        Análisis/Texto base a transformar: "{analisis_manual}"

        Instrucciones de estructura:
        1. Desglosa los requisitos aportados de forma limpia en listas para los campos "minimos" y "recomendados".
        2. El "analisis_detallado" debe constar de 2 párrafos redactados en HTML (<p>...</p>) usando la información del texto base pero con un vocabulario totalmente reestructurado, fluido y técnico.

        Devuelve UNICAMENTE un JSON válido con esta estructura:
        {{
            "fecha": "Fecha de lanzamiento estimada o real del juego",
            "plataformas": "Plataformas en las que está disponible",
            "calificacion": "{calificacion_manual}",
            "motor_grafico": "Motor gráfico que usa (o 'No especificado' si no se deduce)",
            "tecnologias": "Tecnologías de optimización deducidas (DLSS, FSR, Ray Tracing, etc.)",
            "rendimiento": "Resolución y FPS recomendados en base a la lectura",
            "sinopsis": "Una sinopsis breve de 2 líneas escrita con tus palabras.",
            "analisis_detallado": "<p>Primer párrafo reescrito anti-plagio.</p><p>Segundo párrafo técnico reescrito.</p>",
            "requisitos": {{
                "minimos": ["Requisito 1 extraído", "Requisito 2 extraído"],
                "recomendados": ["Requisito 1 extraído", "Requisito 2 extraído"]
            }}
        }}
        """
    else:
        # Modo automático tradicional (Wikipedia)
        contexto_web = buscar_info_extra(titulo)
        prompt = f"""
        Actúa como experto en hardware y rendimiento. Analiza el juego '{titulo}'.
        Contexto oficial extraído: "{contexto_web}"
        
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
            "calificacion": data.get("calificacion", calificacion_manual),
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
            
        print(f"   ✅ {titulo} indexado correctamente.")
        
    except Exception as e:
        print(f"❌ Error en {titulo}: {e}")
        error_msg = str(e).replace('"', "'") 
        
        error_juego = {
            "id": id_juego,
            "titulo": f"⚠️ {titulo}",
            "fecha": "ERROR",
            "plataformas": "N/A",
            "calificacion": calificacion_manual,
            "motor_grafico": "N/A",
            "tecnologias": "N/A",
            "rendimiento": "N/A",
            "sinopsis": "Error en la generación de datos.",
            "analisis_detallado": f"<p class='text-red-400'>Error en transformación: {error_msg}</p>",
            "requisitos": {"minimos": ["N/A"], "recomendados": ["N/A"]},
            "imagen": imagen_real
        }
        idx = next((i for i, j in enumerate(estructura_final["juegos"]) if j["id"] == id_juego), None)
        if idx is not None: estructura_final["juegos"][idx] = error_juego
        else: estructura_final["juegos"].append(error_juego)
    
    time.sleep(12)

# 4. GUARDAR CAMBIOS
with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print("✅ Archivo telemetria.json actualizado exitosamente.")
