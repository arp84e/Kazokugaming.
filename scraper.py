import os
import json
import time
from datetime import datetime, timedelta
import feedparser
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
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
# TAREA 2: SISTEMA DE LANZAMIENTOS (Expansión a 3 Meses)
# ==========================================
hoy = datetime.now()
meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# Función para calcular los meses evitando errores de cambio de año
def obtener_mes_anio(mes_offset):
    fecha_calculada = hoy.replace(day=1) + timedelta(days=30 * mes_offset)
    return f"{meses_nombres[fecha_calculada.month - 1]} {fecha_calculada.year}"

mes_pasado_str = obtener_mes_anio(-1)
mes_actual_str = f"{meses_nombres[hoy.month - 1]} {hoy.year}"
mes_siguiente_str = obtener_mes_anio(1)

print(f"Generando calendario interactivo para: {mes_pasado_str}, {mes_actual_str} y {mes_siguiente_str}...")

prompt_lanzamientos = f"""
Eres un analista experto de la industria de los videojuegos.
Genera una lista de los 4 a 6 lanzamientos de videojuegos más importantes para CADA UNO de estos tres meses: {mes_pasado_str}, {mes_actual_str} y {mes_siguiente_str}.
Devuelve ESTRICTAMENTE un archivo JSON con esta estructura exacta:
{{
  "meses_disponibles": ["{mes_pasado_str}", "{mes_actual_str}", "{mes_siguiente_str}"],
  "catalogo": {{
    "{mes_pasado_str}": [
      {{
        "titulo": "Nombre del Juego",
        "fecha": "Día exacto",
        "plataformas": "PC, PS5, etc.",
        "imagen": "https://placehold.co/600x400/141419/00f0ff.png?text=Nombre+Del+Juego",
        "descripcion": "Descripción de 2 líneas."
      }}
    ],
    "{mes_actual_str}": [ ... ],
    "{mes_siguiente_str}": [ ... ]
  }}
}}
REGLA VITAL PARA LA IMAGEN: Usa EXACTAMENTE el enlace base 'https://placehold.co/600x400/141419/00f0ff.png?text=' y agrégale el nombre del juego al final, cambiando los espacios por signos '+'. Ejemplo: 'https://placehold.co/600x400/141419/00f0ff.png?text=Gears+of+War'. No inventes otras URLs.
"""
try:
    resp_lanzamientos = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_lanzamientos,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    with open('lanzamientos.json', 'w', encoding='utf-8') as f:
        f.write(resp_lanzamientos.text)
    print("¡Éxito! lanzamientos.json de 3 meses creado correctamente.")
except Exception as e:
    print("Error al generar los lanzamientos:", e)
