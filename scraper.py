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
    textos = "".join([f"Título: {e.title}\nResumen: {e.summary}\nEnlace: {e.link}\n\n" for e in nuevas_entradas])
    prompt = f"""Eres un periodista de videojuegos. Reescribe estas noticias al español.
    Genera un JSON con una lista "nuevas_noticias".
    Formato: {{"nuevas_noticias": [ {{"categoria": "...", "titulo": "...", "resumen": "...", "contenido_completo": "<p>...</p>", "imagen": "URL de unsplash gaming", "enlace": "..."}} ] }}
    Noticias:\n{textos}"""
    
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
# TAREA 2: SISTEMA DE LANZAMIENTOS (NUEVO)
# ==========================================
mes_actual = datetime.now().month
anio_actual = datetime.now().year
print(f"Generando calendario de lanzamientos para {mes_actual}/{anio_actual}...")

prompt_lanzamientos = f"""
Eres un analista de la industria de los videojuegos.
Busca y genera una lista de los 6 a 8 lanzamientos de videojuegos más importantes y esperados para el mes actual ({mes_actual}/{anio_actual}).
Devuelve ESTRICTAMENTE un archivo JSON con esta estructura:
{{
  "mes": "Nombre del mes actual en español (ej: Mayo 2026)",
  "lanzamientos": [
    {{
      "titulo": "Nombre del Juego",
      "fecha": "Día exacto (ej: 15 de Mayo)",
      "plataformas": "PS5, Xbox Series, PC",
      "imagen": "URL de Unsplash sobre videojuegos, consolas o cyberpunk",
      "descripcion": "Breve descripción de 2 líneas sobre de qué trata el juego."
    }}
  ]
}}
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
