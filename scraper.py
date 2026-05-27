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
    REGLA DE IMÁGENES: Usa la URL de la "Imagen oficial" que te doy. Si está vacía o no hay enlace, usa ESTA URL OBLIGATORIAMENTE: https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80
    
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
# TAREA 2: SISTEMA DE LANZAMIENTOS
# ==========================================
meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
mes_actual = datetime.now().month
anio_actual = datetime.now().year
nombre_mes = f"{meses[mes_actual-1]} {anio_actual}"

print(f"Generando calendario de lanzamientos para {nombre_mes}...")

prompt_lanzamientos = f"""
Eres un experto en videojuegos. Genera una lista de los 6 lanzamientos más importantes para {nombre_mes}.
Devuelve un JSON estrictamente con esta estructura:
{{
  "mes": "{nombre_mes}",
  "lanzamientos": [
    {{
      "titulo": "Nombre del Juego",
      "fecha": "Día exacto",
      "plataformas": "PS5, Xbox Series, PC",
      "imagen": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=500&q=80",
      "descripcion": "Descripción corta de 2 líneas."
    }}
  ]
}}
IMPORTANTE: Para "imagen", usa fotos genéricas de Unsplash sobre tecnología (ej: https://images.unsplash.com/photo-1612287230202-1bf1d85d1bdf?auto=format&fit=crop&w=500&q=80). Nunca dejes esto vacío.
"""
try:
    resp_lanzamientos = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_lanzamientos,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    with open('lanzamientos.json', 'w', encoding='utf-8') as f:
        f.write(resp_lanzamientos.text)
    print("¡Éxito! lanzamientos.json creado correctamente.")
except Exception as e:
    print("Error al generar los lanzamientos:", e)
