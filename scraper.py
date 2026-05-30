import os
import json
import time
from datetime import datetime, timedelta
import feedparser
import requests  # Asegúrate de que tu entorno/workflow tenga 'requests' instalado
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")  # Tu clave de RAWG

client = genai.Client(api_key=api_key)

# Variables globales para fechas
hoy = datetime.now()
meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# ==========================================
# TAREA 1: SISTEMA DE NOTICIAS
# ==========================================
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

print("Buscando noticias nuevas...")
feed = feedparser.parse("https://feeds.feedburner.com/ign/games-all")
nuevas_entradas = [e for e in feed.entries if e.link not in enlaces_guardados][:3]
noticias_totales = noticias_validas

if nuevas_entradas:
    textos = ""
    for e in nuevas_entradas:
        img = ""
        if 'media_content' in e and len(e.media_content) > 0: img = e.media_content[0]['url']
        elif 'media_thumbnail' in e and len(e.media_thumbnail) > 0: img = e.media_thumbnail[0]['url']
        textos += f"Título: {e.title}\nResumen: {e.summary}\nEnlace: {e.link}\nImagen oficial: {img}\n\n"
        
    prompt = f"""Eres un periodista de videojuegos. Reescribe estas noticias al español de forma detallada.
    Genera un JSON con una lista llamada "nuevas_noticias".
    REGLA DE IMÁGENES: Usa la URL de la "Imagen oficial" que te doy. Si está vacía, usa obligatoriamente esta URL: https://placehold.co/1200x600/141419/00f0ff.png?text=Noticia+Gaming
    
    Formato: {{"nuevas_noticias": [ {{"categoria": "...", "titulo": "...", "resumen": "...", "contenido_completo": "<p>...</p>", "imagen": "AQUI LA URL", "enlace": "..."}} ] }}
    Noticias a procesar:\n{textos}"""
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        noticias_ia = json.loads(response.text).get("nuevas_noticias", [])
        for i, n in enumerate(noticias_ia):
            n['fecha'] = datetime.now().isoformat()
            n['id'] = f"not_{int(time.time())}_{i}"
        noticias_totales = noticias_ia + noticias_validas
    except Exception as e: print("Error en noticias:", e)

# CORREGIDO: Se cerró correctamente el flujo de escritura de noticias
if noticias_totales:
    try:
        with open('noticias.json', 'w', encoding='utf-8') as f:
            json.dump({"destacada": noticias_totales[0], "secundarias": noticias_totales[1:]}, f, ensure_ascii=False, indent=2)
    except Exception as e:
         print("Error al guardar noticias.json:", e)


# ==========================================
# FUNCIÓN AUXILIAR: BUSCADOR DE IMÁGENES REALES (RAWG)
# ==========================================
# REINCORPORADA: Esta función faltaba por completo en tu código cortado
def buscar_portada_juego(titulo_juego):
    if not rawg_key:
        print("Advertencia: No se encontró RAWG_API_KEY. Usando imagen por defecto.")
        return ""
    
    try:
        url = f"https://api.rawg.io/api/games?key={rawg_key}&search={titulo_juego}&page_size=1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                return data["results"][0].get("background_image", "")
    except Exception as e:
        print(f"Error al buscar imagen para {titulo_juego}:", e)
    return ""


# ==========================================
# TAREA 2: SISTEMA DE LANZAMIENTOS (MÉTODO DE DOS PASOS)
# ==========================================
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

print(f"--- PASO 1: Investigando lanzamientos reales en internet ---")

prompt_busqueda = f"""
Usa Google Search para investigar en portales líderes de videojuegos (IGN, Vandal, 3DJuegos, Eurogamer) el calendario oficial de lanzamientos.
Necesito que listes de forma exhaustiva los videojuegos con FECHA EXACTA CONFIRMADA para estos tres meses:
- {mes_pasado_str}
- {mes_actual_str}
- {mes_siguiente_str}

REGLAS:
1. Solo incluye juegos con día y mes confirmados. Descarta rumores o aproximaciones ("Q3", "2026", etc.).
2. Incluye tanto títulos AAA como juegos indies importantes.
3. Devuelve la información organizada en texto claro, detallando para cada juego: Título, Fecha exacta, Plataformas y una breve descripción en español.
"""

try:
    respuesta_busqueda = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_busqueda,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )
    
    texto_investigacion = respuesta_busqueda.text
    print(">> Investigación completada con éxito. Procesando estructura...")

    print(f"--- PASO 2: Convirtiendo datos a formato JSON para la Web ---")
    
    prompt_estructurar = f"""
    Toma la siguiente información de lanzamientos de videojuegos y conviértela ESTRICTAMENTE en un objeto JSON.
    
    Información a procesar:
    {texto_investigacion}
    
    Estructura JSON exacta requerida:
    {{
      "meses_disponibles": ["{mes_pasado_str}", "{mes_actual_str}", "{mes_siguiente_str}"],
      "catalogo": {{
        "{mes_pasado_str}": [
          {{
            "titulo": "Nombre del Juego",
            "fecha": "Día exacto",
            "plataformas": "Plataformas",
            "descripcion": "Descripción corta de 2-3 líneas en español."
          }}
        ],
        "{mes_actual_str}": [
          {{
            "titulo": "Nombre del Juego",
            "fecha": "Día exacto",
            "plataformas": "Plataformas",
            "descripcion": "Descripción..."
          }}
        ],
        "{mes_siguiente_str}": [
          {{
            "titulo": "Nombre del Juego",
            "fecha": "Día exacto",
            "plataformas": "Plataformas",
            "descripcion": "Descripción..."
          }}
        ]
      }}
    }}
    Nota: No agregues ninguna clave llamada "imagen" en este paso.
    """

    respuesta_json = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_estructurar,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    estructura_json = json.loads(respuesta_json.text)
    
    if "meses_disponibles" in estructura_json and "catalogo" in estructura_json:
        for mes in estructura_json["meses_disponibles"]:
            if mes in estructura_json["catalogo"]:
                print(f">> Insertando imágenes para {len(estructura_json['catalogo'][mes])} juegos de {mes}.")
                for juego in estructura_json["catalogo"][mes]:
                    titulo = juego["titulo"]
                    
                    url_imagen_real = buscar_portada_juego(titulo)
                    juego["imagen"] = url_imagen_real
                    time.sleep(0.25)
                    
        with open('lanzamientos.json', 'w', encoding='utf-8') as f:
            json.dump(estructura_json, f, ensure_ascii=False, indent=2)
            
        print("¡Éxito absoluto! El archivo lanzamientos.json se ha creado correctamente.")
    else:
        print("Error: El formateador no devolvió las llaves esperadas.")

except Exception as e:
    print("Error crítico en el proceso de lanzamientos:", e)
