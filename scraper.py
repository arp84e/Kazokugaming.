import os
import feedparser
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Buscando noticias...")
feed_url = "https://feeds.feedburner.com/ign/games-all"
feed = feedparser.parse(feed_url)

entradas = feed.entries[:3]
textos_noticias = ""
for i, entry in enumerate(entradas):
    # ¡NUEVO! Intentamos extraer la imagen real y oficial de la noticia
    imagen_original = ""
    if 'media_content' in entry and len(entry.media_content) > 0:
        imagen_original = entry.media_content[0]['url']
    elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        imagen_original = entry.media_thumbnail[0]['url']
    
    textos_noticias += f"Noticia {i+1}:\nTítulo: {entry.title}\nResumen: {entry.summary}\nEnlace original: {entry.link}\nImagen oficial: {imagen_original}\n\n"

# Instrucciones actualizadas para artículos largos e imágenes reales
prompt = f"""
Eres un periodista experto y analista de videojuegos para KazokuGaming.
Lee estas 3 noticias en inglés y haz lo siguiente:
1. Usa la Noticia 1 como "destacada" y las Noticias 2 y 3 como "secundarias".
2. Reescribe y traduce al español con un tono gamer profesional, analítico y profundo.
3. CONTENIDO MÁS COMPLETO: En el campo "contenido_completo", redacta un artículo extenso (de 4 a 6 párrafos). No solo resumas; incluye el contexto de la noticia, por qué es importante para la comunidad, y detalles clave. Usa etiquetas HTML <p> para separar párrafos, y usa <strong> para resaltar los nombres de los juegos o datos importantes.
4. IMÁGENES EXACTAS: En el campo "imagen", DEBES poner exactamente la URL que dice "Imagen oficial" en la información que te paso. Si por algún motivo está vacía, solo entonces inventa una URL de Unsplash.

Estructura JSON requerida ESTRICTAMENTE:
{{
  "destacada": {{
    "id": "destacada",
    "categoria": "Categoría (ej: RPG, Shooter, Industria)",
    "titulo": "Título atractivo y adaptado",
    "resumen": "Resumen detallado de 3 líneas",
    "contenido_completo": "<p>Primer párrafo introductorio...</p><p>Segundo párrafo con <strong>detalles clave</strong>...</p><p>Tercer párrafo de contexto...</p><p>Párrafo final y conclusiones...</p>",
    "imagen": "URL de la Imagen oficial",
    "enlace": "Enlace original"
  }},
  "secundarias": [
    {{
      "id": "sec1",
      "categoria": "Categoría",
      "titulo": "Título de noticia 2",
      "resumen": "Resumen detallado",
      "contenido_completo": "<p>Párrafo 1...</p><p>Párrafo 2...</p><p>Párrafo 3...</p><p>Párrafo 4...</p>",
      "imagen": "URL de la Imagen oficial de la noticia 2",
      "enlace": "Enlace original"
    }},
    {{
      "id": "sec2",
      "categoria": "Categoría",
      "titulo": "Título de noticia 3",
      "resumen": "Resumen detallado",
      "contenido_completo": "<p>Párrafo 1...</p><p>Párrafo 2...</p><p>Párrafo 3...</p><p>Párrafo 4...</p>",
      "imagen": "URL de la Imagen oficial de la noticia 3",
      "enlace": "Enlace original"
    }}
  ]
}}

Noticias a procesar:
{textos_noticias}
"""

print("Enviando a Gemini para redacción completa y extracción de imágenes...")
try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    with open('noticias.json', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("¡Éxito! noticias.json creado correctamente con imágenes reales y textos largos.")
except Exception as e:
    print(f"Error crítico en la IA: {e}")
