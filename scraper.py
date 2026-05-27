import os
import json
import time
from datetime import datetime, timedelta
import feedparser
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

archivo_json = 'noticias.json'
historial = []

# 1. Leer el historial guardado para no borrarlo
if os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'destacada' in data:
                historial.append(data['destacada'])
            if 'secundarias' in data:
                historial.extend(data['secundarias'])
    except Exception as e:
        print("No se pudo leer el archivo anterior.", e)

# 2. Filtrar el historial (Eliminar las que tengan más de 3 días)
fecha_limite = datetime.now() - timedelta(days=3)
noticias_validas = []
enlaces_guardados = set()

for noticia in historial:
    # Si la noticia es antigua y no tiene fecha, le ponemos la de hoy para no perderla
    fecha_str = noticia.get('fecha', datetime.now().isoformat())
    try:
        fecha_obj = datetime.fromisoformat(fecha_str)
    except:
        fecha_obj = datetime.now()
        
    if fecha_obj > fecha_limite:
        noticia['fecha'] = fecha_obj.isoformat()
        noticias_validas.append(noticia)
        enlaces_guardados.add(noticia.get('enlace', ''))

# 3. Buscar noticias nuevas en IGN
print("Buscando noticias nuevas...")
feed = feedparser.parse("https://feeds.feedburner.com/ign/games-all")
nuevas_entradas = []

for entry in feed.entries:
    # Solo tomamos la noticia si no la habíamos guardado antes
    if entry.link not in enlaces_guardados:
        nuevas_entradas.append(entry)
    if len(nuevas_entradas) >= 3: # Tomar un máximo de 3 nuevas por ejecución
        break

# 4. Procesar con IA si hay contenido nuevo
noticias_totales = noticias_validas

if len(nuevas_entradas) > 0:
    textos = ""
    for i, entry in enumerate(nuevas_entradas):
        imagen = ""
        if 'media_content' in entry and len(entry.media_content) > 0:
            imagen = entry.media_content[0]['url']
        elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
            imagen = entry.media_thumbnail[0]['url']
            
        textos += f"Noticia {i+1}:\nTitulo: {entry.title}\nResumen: {entry.summary}\nEnlace: {entry.link}\nImagen: {imagen}\n\n"

    prompt = f"""
    Eres un periodista de videojuegos para KazokuGaming.
    Reescribe estas noticias al español con un tono gamer, analítico y profesional.
    Genera un JSON con una lista (array) llamada "nuevas_noticias".
    
    {{
      "nuevas_noticias": [
         {{
            "categoria": "Categoría (Ej: RPG, Hardware)",
            "titulo": "Título adaptado",
            "resumen": "Resumen de 3 líneas",
            "contenido_completo": "<p>Párrafo 1...</p><p>Párrafo 2...</p><p>Párrafo 3...</p><p>Párrafo 4...</p>",
            "imagen": "URL de la imagen proporcionada",
            "enlace": "Enlace original"
         }}
      ]
    }}
    
    Noticias a procesar:
    {textos}
    """
    
    try:
        print("Traduciendo y redactando artículos...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        resultado_ia = json.loads(response.text)
        noticias_ia = resultado_ia.get("nuevas_noticias", [])
        
        # Generar IDs únicos y estampar la hora exacta de publicación
        fecha_actual = datetime.now().isoformat()
        marca_tiempo = str(int(time.time()))
        
        for i, n in enumerate(noticias_ia):
            n['fecha'] = fecha_actual
            n['id'] = f"not_{marca_tiempo}_{i}"
            
        # Unir las nuevas (que irán arriba del todo) con el historial válido
        noticias_totales = noticias_ia + noticias_validas
        print(f"¡Se agregaron {len(noticias_ia)} noticias nuevas al catálogo!")
    except Exception as e:
        print("Error al procesar con IA:", e)
else:
    print("No hay noticias nuevas en este momento. Se mantiene el historial intacto.")

# 5. Guardar el archivo final estructurado para la web
if len(noticias_totales) > 0:
    json_final = {
        "destacada": noticias_totales[0], # La más nueva de todas va en el Banner Principal
        "secundarias": noticias_totales[1:] # Todo el resto (nuevas y antiguas) van a las tarjetas
    }
    with open('noticias.json', 'w', encoding='utf-8') as f:
        json.dump(json_final, f, ensure_ascii=False, indent=2)
    print(f"Éxito: Archivo guardado con {len(noticias_totales)} artículos en total.")
