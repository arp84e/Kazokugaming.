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
    textos_noticias += f"Noticia {i+1}:\nTítulo: {entry.title}\nResumen: {entry.summary}\nEnlace original: {entry.link}\n\n"

prompt = f"""
Eres un periodista experto en videojuegos para KazokuGaming.
Lee estas 3 noticias en inglés y haz lo siguiente:
1. Usa la Noticia 1 como "destacada".
2. Usa las Noticias 2 y 3 como "secundarias".
3. Reescribe y traduce al español con un tono gamer profesional.
4. MUY IMPORTANTE: Además del resumen, escribe un "contenido_completo" extenso (de 3 a 4 párrafos bien redactados, usando etiquetas HTML <p> para separar los párrafos).

Estructura JSON requerida ESTRICTAMENTE:
{{
  "destacada": {{
    "id": "destacada",
    "categoria": "Lanzamiento",
    "titulo": "Título de la noticia",
    "resumen": "Resumen corto de 2 líneas",
    "contenido_completo": "<p>Primer párrafo extenso...</p><p>Segundo párrafo detallado...</p><p>Tercer párrafo de cierre...</p>",
    "imagen": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80",
    "enlace": "Enlace original"
  }},
  "secundarias": [
    {{
      "id": "sec1",
      "categoria": "Rumor",
      "titulo": "Título de noticia 2",
      "resumen": "Resumen corto",
      "contenido_completo": "<p>Párrafo 1...</p><p>Párrafo 2...</p>",
      "imagen": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=500&q=80",
      "enlace": "Enlace original"
    }},
    {{
      "id": "sec2",
      "categoria": "Actualización",
      "titulo": "Título de noticia 3",
      "resumen": "Resumen corto",
      "contenido_completo": "<p>Párrafo 1...</p><p>Párrafo 2...</p>",
      "imagen": "https://images.unsplash.com/photo-1612287230202-1bf1d85d1bdf?auto=format&fit=crop&w=500&q=80",
      "enlace": "Enlace original"
    }}
  ]
}}

Noticias a procesar:
{textos_noticias}
"""

print("Enviando a Gemini para redacción completa...")
try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    with open('noticias.json', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("¡Éxito! noticias.json creado correctamente.")
except Exception as e:
    print(f"Error crítico en la IA: {e}")
