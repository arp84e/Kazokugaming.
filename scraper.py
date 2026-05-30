import os
import json
import time
from datetime import datetime, timedelta
import feedparser
import requests  # Asegúrate de que tu entorno/workflow tenga 'requests' instalado
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")  # Tu nueva clave de RAWG

client = genai.Client(api_key=api_key)

# ==========================================
# TAREA 1: SISTEMA DE NOTICIAS (Se mantiene igual)
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

if noticias_totales:
    with open('noticias.json', 'w', encoding='utf-8') as f:
        json.dump({"destacada": noticias_totales[0], "secundarias": noticias_totales[1:]}, f, ensure_ascii=False, indent=2)


# ==========================================
# FUNCIÓN AUXILIAR: BUSCADOR DE IMÁGENES REALES (RAWG)
# ==========================================
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
                # Extrae la imagen de fondo oficial del juego (background_image)
                return data["results"][0].get("background_image", "")
    except Exception as e:
        print(f"Error al buscar imagen para {titulo_juego}:", e)
    return ""


# ==========================================
# TAREA 2: SISTEMA DE LANZAMIENTOS (Modificado para traer lista completa)
# ==========================================
hoy = datetime.now()
meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

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

print(f"Generando calendario para: {mes_pasado_str}, {mes_actual_str} y {mes_siguiente_str}...")

# Se modificó la instrucción para pedir TODOS los lanzamientos sin límite numérico
prompt_lanzamientos = f"""
Eres un analista experto de la industria de los videojuegos.
Genera una lista exhaustiva que incluya TODOS los lanzamientos de videojuegos importantes (tanto triples A como juegos indie destacados) para CADA UNO de estos tres meses distintos: '{mes_pasado_str}', '{mes_actual_str}' y '{mes_siguiente_str}'. No te limites a un número pequeño, incluye la lista completa disponible en tu base de conocimiento.

Devuelve ESTRICTAMENTE un archivo JSON con esta estructura exacta:
{{
  "meses_disponibles": ["{mes_pasado_str}", "{mes_actual_str}", "{mes_siguiente_str}"],
  "catalogo": {{
    "{mes_pasado_str}": [
      {{
        "titulo": "Nombre del Juego Real",
        "fecha": "Día exacto",
        "plataformas": "PC, PS5, etc.",
        "descripcion": "Descripción de 2 líneas."
      }}
    ],
    "{mes_actual_str}": [
      {{
        "titulo": "Nombre del Juego Actual Real",
        "fecha": "Día exacto",
        "plataformas": "PC, Xbox, etc.",
        "descripcion": "Descripción..."
      }}
    ],
    "{mes_siguiente_str}": [
      {{
        "titulo": "Nombre del Juego Futuro Real",
        "fecha": "Día exacto",
        "plataformas": "Switch, PC, etc.",
        "descripcion": "Descripción..."
      }}
    ]
  }}
}}
Nota: No agregues el campo imagen en este prompt, el sistema de Python se encargará de inyectarlo mediante API externa.
"""

try:
    resp_lanzamientos = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_lanzamientos,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    
    # Convertimos la respuesta de Gemini en un diccionario manipulable de Python
    estructura_json = json.loads(resp_lanzamientos.text)
    
    # Sincronizamos las imágenes reales usando la API de RAWG juego por juego
    for mes in estructura_json["meses_disponibles"]:
        if mes in estructura_json["catalogo"]:
            for juego in estructura_json["catalogo"][mes]:
                titulo = juego["titulo"]
                print(f"Buscando arte oficial para: {titulo}...")
                
                # Llamada a la API de imágenes
                url_imagen_real = buscar_portada_juego(titulo)
                
                # Inyectamos el campo dinámicamente
                juego["imagen"] = url_imagen_real
                time.sleep(0.2) # Pausa de cortesía para la API
                
    # Guardamos el archivo final enriquecido
    with open('lanzamientos.json', 'w', encoding='utf-8') as f:
        json.dump(estructura_json, f, ensure_ascii=False, indent=2)
        
    print("¡Éxito! lanzamientos.json con portadas reales y verificadas creado correctamente.")

except Exception as e:
    print("Error al generar los lanzamientos:", e)
