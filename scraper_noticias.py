import os
import sys
import json
import feedparser
from datetime import datetime
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: NOTICIAS ===")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

seguridad_permisiva = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

rss_url = "https://es.ign.com/feed.xml" # Puedes sustituir esta URL por tu fuente principal
feed = feedparser.parse(rss_url)

if not feed.entries:
    print("❌ No se detectaron entradas en el feed proporcionado.")
    sys.exit(1)

noticia_origen = feed.entries[0]
print(f"Procesando la noticia principal: {noticia_origen.title}")

prompt_noticias = f"""
Actúa como un editor principal de una revista de videojuegos. Redacta un artículo periodístico basado en lo siguiente:
Título original: {noticia_origen.title}
Fuente/Enlace: {noticia_origen.link}

Genera UNICAMENTE un objeto JSON válido con esta estructura exacta:
{{
  "destacada": {{
    "categoria": "Noticias de Videojuegos",
    "titulo": "Un título editorial potente",
    "resumen": "Resumen conciso del acontecimiento.",
    "contenido_completo": "<p>Escribe aquí 3 o 4 párrafos en HTML detallando la noticia e incorporando tu propio enfoque sobre el impacto en la industria o rendimiento esperado.</p>",
    "imagen": "Genera una URL de imagen ilustrativa genérica si no hay portada",
    "enlace": "{noticia_origen.link}",
    "fecha": "{datetime.now().isoformat()}"
  }}
}}
"""

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_noticias,
        config=types.GenerateContentConfig(
            safety_settings=seguridad_permisiva,
            response_mime_type="application/json",
        )
    )
    
    noticias_data = json.loads(response.text)
    
    with open('noticias.json', 'w', encoding='utf-8') as f:
        json.dump(noticias_data, f, ensure_ascii=False, indent=2)
        
    print("✅ noticias.json redactado y guardado correctamente.")
    
except Exception as e:
    print(f"⚠️ Error durante la redacción de la noticia: {e}")
