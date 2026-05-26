import os
import feedparser
import google.generativeai as genai

# 1. Conectar con la bóveda secreta de GitHub
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Usamos la versión más rápida y especializada en datos de Gemini
model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})

# 2. Leer las noticias internacionales (Ejemplo: IGN)
print("Buscando noticias...")
feed_url = "https://feeds.feedburner.com/ign/games-all"
feed = feedparser.parse(feed_url)

# Tomamos las 3 noticias más recientes
entradas = feed.entries[:3]
textos_noticias = ""
for i, entry in enumerate(entradas):
    textos_noticias += f"Noticia {i+1}:\nTítulo: {entry.title}\nResumen: {entry.summary}\nEnlace original: {entry.link}\n\n"

# 3. Instrucciones estrictas para la IA (Tu Redactor Jefe)
prompt = f"""
Eres un periodista experto en videojuegos para la revista hispanohablante KazokuGaming.
Aquí tienes 3 noticias recientes en inglés. Tu trabajo es:
1. Usar la Noticia 1 como la "destacada".
2. Usar las Noticias 2 y 3 como "secundarias".
3. Reescribir y traducir los textos al español neutro con un tono gamer, dinámico y original para evitar problemas de copyright. NO traduzcas literalmente.
4. Generar UN ÚNICO archivo JSON estrictamente con esta estructura. Usa enlaces de imágenes de Unsplash relacionados con gaming (neón, consolas, teclados) para ilustrarlas de forma legal.

Estructura JSON requerida:
{{
  "destacada": {{
    "categoria": "Palabra clave (ej: Lanzamiento)",
    "titulo": "Tu nuevo título atractivo",
    "resumen": "Resumen adaptado de 3 líneas",
    "imagen": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80",
    "enlace": "Enlace original de la noticia"
  }},
  "secundarias": [
    {{
      "categoria": "Palabra clave",
      "titulo": "Título adaptado",
      "resumen": "Resumen de 2 líneas",
      "imagen": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=500&q=80",
      "enlace": "Enlace original de la noticia"
    }},
    {{
      "categoria": "Palabra clave",
      "titulo": "Título adaptado",
      "resumen": "Resumen de 2 líneas",
      "imagen": "https://images.unsplash.com/photo-1612287230202-1bf1d85d1bdf?auto=format&fit=crop&w=500&q=80",
      "enlace": "Enlace original de la noticia"
    }}
  ]
}}

Noticias a procesar:
{textos_noticias}
"""

# 4. Generar y guardar
print("Enviando a Gemini para traducción y adaptación...")
try:
    response = model.generate_content(prompt)
    with open('noticias.json', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("¡Éxito! noticias.json creado correctamente.")
except Exception as e:
    print(f"Error crítico en la IA: {e}")
