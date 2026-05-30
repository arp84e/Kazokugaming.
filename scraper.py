import os
import sys
import json
import time
from datetime import datetime, timedelta
import feedparser
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT ===")

# Validar que las variables de entorno existan
api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")

if not api_key:
    print("❌ ERROR CRÍTICO: No se encontró GEMINI_API_KEY. Verifica los Secrets de GitHub.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# Variables globales para fechas
hoy = datetime.now()
meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# ==========================================
# FILTROS DE SEGURIDAD GLOBALES (CRÍTICO PARA JUEGOS)
# Evita que la IA se bloquee al leer sobre juegos de acción o shooters
# ==========================================
seguridad_permisiva = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

# ==========================================
# TAREA 1: SISTEMA DE NOTICIAS
# ==========================================
print("\n--- EJECUTANDO TAREA 1: NOTICIAS ---")
archivo_json = 'noticias.json'
historial = []

if os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'destacada' in data: historial.append(data['destacada'])
            if 'secundarias' in data: historial.extend(data['secundarias'])
    except: pass

fecha_limite = datetime.now() - timedelta(days=3)
noticias_validas = []
enlaces_guardados = set()

for noticia in historial:
    fecha_str = noticia.get('fecha', datetime.now().isoformat())
    try: fecha_obj = datetime.fromisoformat(fecha_str)
    except: fecha_obj = datetime.now()
        
    if fecha_obj > fecha_limite:
        noticia['fecha'] = fecha_obj.isoformat()
        noticias_validas.append(noticia)
        enlaces_guardados.add(noticia.get('enlace', ''))

feed = feedparser.parse("https://feeds.feedburner.com/ign/games-all")
nuevas_entradas = [e for e in feed.entries if e.link not in enlaces_guardados][:3]
noticias_totales = noticias_validas

if nuevas_entradas:
    print(f">> Procesando {len(nuevas_entradas)} noticias nuevas...")
    textos = ""
    for e in nuevas_entradas:
        img = ""
        if 'media_content' in e and len(e.media_content) > 0: img = e.media_content[0]['url']
        elif 'media_thumbnail' in e and len(e.media_thumbnail) > 0: img = e.media_thumbnail[0]['url']
        textos += f"Título: {e.title}\nResumen: {e.summary}\nEnlace: {e.link}\nImagen oficial: {img}\n\n"
        
    prompt = f"""Eres un periodista de videojuegos. Reescribe estas noticias al español de forma detallada.
    Genera un JSON con una lista llamada "nuevas_noticias". Formato: {{"nuevas_noticias": [ {{"categoria": "...", "titulo": "...", "resumen": "...", "contenido_completo": "<p>...</p>", "imagen": "URL", "enlace": "..."}} ] }}
    Noticias a procesar:\n{textos}"""
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                safety_settings=seguridad_permisiva # Añadido filtro
            )
        )
        
        texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
        noticias_ia = json.loads(texto_limpio).get("nuevas_noticias", [])
        
        for i, n in enumerate(noticias_ia):
            n['fecha'] = datetime.now().isoformat()
            n['id'] = f"not_{int(time.time())}_{i}"
        noticias_totales = noticias_ia + noticias_validas
    except Exception as e: 
        print("❌ Error procesando noticias:", e)

if noticias_totales:
    try:
        with open('noticias.json', 'w', encoding='utf-8') as f:
            json.dump({"destacada": noticias_totales[0], "secundarias": noticias_totales[1:]}, f, ensure_ascii=False, indent=2)
        print("✅ noticias.json actualizado correctamente.")
    except Exception as e:
        print("❌ Error al guardar noticias.json:", e)


# ==========================================
# FUNCIÓN AUXILIAR: BUSCADOR DE IMÁGENES (RAWG)
# ==========================================
def buscar_portada_juego(titulo_juego):
    if not rawg_key: return ""
    try:
        url = f"https://api.rawg.io/api/games?key={rawg_key}&search={titulo_juego}&page_size=1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("results"): return data["results"][0].get("background_image", "")
    except Exception: pass
    return ""


# ==========================================
# TAREA 2: SISTEMA DE LANZAMIENTOS (MÉTODO BLINDADO + DOBLE INTENTO)
# ==========================================
print("\n--- EJECUTANDO TAREA 2: LANZAMIENTOS ---")

def calcular_mes_exacto(offset):
    mes_calculado = hoy.month + offset
    anio_calculado = hoy.year
    while mes_calculado < 1:
        mes_calculado += 12
        anio_calculado -= 1
    while mes_calculado > 12:
        mes_calculado -= 12
        anio_calculado += 1
    return f"{meses_nombres[mes_calculado - 1]} {anio_calculado}"

mes_pasado_str = calcular_mes_exacto(-1)
mes_actual_str = f"{meses_nombres[hoy.month - 1]} {hoy.year}"
mes_siguiente_str = calcular_mes_exacto(1)

# Estructura de seguridad (Fallback). 
estructura_final = {
    "meses_disponibles": [mes_pasado_str, mes_actual_str, mes_siguiente_str],
    "catalogo": { mes_pasado_str: [], mes_actual_str: [], mes_siguiente_str: [] }
}

try:
    print(">> Paso 1: Buscando información de lanzamientos...")
    # Flexibilizamos el prompt para que NO devuelva listas vacías
    prompt_busqueda = f"""
    Haz una lista exhaustiva de los lanzamientos de videojuegos más importantes para estos meses: {mes_pasado_str}, {mes_actual_str} y {mes_siguiente_str}.
    Reglas:
    1. Incluye tanto juegos Triple A como juegos Indies destacados.
    2. ¡OBLIGATORIO! Si un juego importante se lanza ese mes pero no tiene el día exacto confirmado, pon "Por confirmar" en la fecha, PERO INCLÚYELO EN LA LISTA. No dejes ningún mes vacío.
    """
    
    try:
        # Intento A: Con búsqueda en Internet en tiempo real
        respuesta_busqueda = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_busqueda,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                safety_settings=seguridad_permisiva
            )
        )
        print("✅ Búsqueda web completada.")
    except Exception as e_search:
        # Intento B: Si la búsqueda web falla por restricciones de la API, usa la base de datos interna de Gemini
        print(f"⚠️ La búsqueda web falló o está restringida en tu API Key: {e_search}")
        print(">> Intentando método alternativo (Memoria interna de la IA)...")
        respuesta_busqueda = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_busqueda,
            config=types.GenerateContentConfig(safety_settings=seguridad_permisiva)
        )
        print("✅ Búsqueda interna completada.")
    
    texto_investigacion = respuesta_busqueda.text
    time.sleep(2) 
    
    print(">> Paso 2: Estructurando los datos a JSON...")
    prompt_estructurar = f"""
    Convierte la siguiente información en un objeto JSON estricto:
    {texto_investigacion}
    
    Formato EXACTO y OBLIGATORIO:
    {{
      "meses_disponibles": ["{mes_pasado_str}", "{mes_actual_str}", "{mes_siguiente_str}"],
      "catalogo": {{
        "{mes_pasado_str}": [ {{"titulo": "Juego A", "fecha": "12 de X", "plataformas": "PC", "descripcion": "..."}} ],
        "{mes_actual_str}": [ {{"titulo": "Juego B", "fecha": "Por confirmar", "plataformas": "PS5", "descripcion": "..."}} ],
        "{mes_siguiente_str}": []
      }}
    }}
    """
    respuesta_json = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_estructurar,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            safety_settings=seguridad_permisiva
        )
    )
    
    texto_json_limpio = respuesta_json.text.replace('```json', '').replace('```', '').strip()
    datos_extraidos = json.loads(texto_json_limpio)
    
    if "catalogo" in datos_extraidos:
        estructura_final = datos_extraidos
        print("✅ JSON estructurado correctamente.")
        
        print(">> Paso 3: Sincronizando portadas de RAWG...")
        for mes in estructura_final.get("meses_disponibles", []):
            juegos_del_mes = estructura_final.get("catalogo", {}).get(mes, [])
            for juego in juegos_del_mes:
                juego["imagen"] = buscar_portada_juego(juego.get("titulo", ""))
                time.sleep(0.25)
        print("✅ Imágenes sincronizadas.")

except Exception as e:
    print(f"⚠️ ERROR DETECTADO EN EL PROCESO GLOBAL: {e}")
    print("Se usará la estructura vacía de emergencia.")

# Escribir en disco
try:
    with open('lanzamientos.json', 'w', encoding='utf-8') as f:
        json.dump(estructura_final, f, ensure_ascii=False, indent=2)
    print("\n✅ lanzamientos.json guardado en disco con éxito.")
except Exception as e:
    print("\n❌ ERROR FATAL AL ESCRIBIR EN DISCO:", e)
    sys.exit(1)

print("=== KAZOKUBOT FINALIZADO CORRECTAMENTE ===")
