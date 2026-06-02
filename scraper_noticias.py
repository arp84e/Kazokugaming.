import os
import sys
import json
import time
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

rss_url = "https://es.ign.com/feed.xml"
feed = feedparser.parse(rss_url)

if not feed.entries:
    print("❌ No se detectaron entradas en el feed.")
    sys.exit(1)

# 🛠️ FUNCIÓN VITAL: Extraer la imagen real del RSS en lugar de pedírsela a la IA
def obtener_imagen(entrada):
    if 'media_content' in entrada and len(entrada.media_content) > 0:
        return entrada.media_content[0]['url']
    if 'media_thumbnail' in entrada and len(entrada.media_thumbnail) > 0:
        return entrada.media_thumbnail[0]['url']
    if 'links' in entrada:
        for link in entrada.links:
            if 'image' in link.get('type', ''):
                return link.href
    # Imagen de respaldo por si la noticia no trae foto
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"

datos_finales = {"destacada": {}, "secundarias": []}

# ==========================================
# 1. PROCESAR LA NOTICIA DESTACADA
# ==========================================
noticia_origen = feed.entries[0]
imagen_real = obtener_imagen(noticia_origen)
print(f"Procesando Destacada: {noticia_origen.title}")

prompt_destacada = f"""
Actúa como un editor principal de videojuegos. Redacta un artículo basado en:
Título: {noticia_origen.title}
Devuelve UNICAMENTE un objeto JSON válido con esta estructura:
{{
  "id": "dest-01",
  "categoria": "Noticia Principal",
  "titulo": "Título potente",
  "resumen": "Resumen corto.",
  "contenido_completo": "<p>Escribe aquí 2 párrafos detallando la noticia en HTML.</p>",
  "enlace": "{noticia_origen.link}",
  "fecha": "{datetime.now().isoformat()}"
}}
"""

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_destacada,
        config=types.GenerateContentConfig(safety_settings=seguridad_permisiva, response_mime_type="application/json")
    )
    datos_dest = json.loads(response.text)
    datos_dest["imagen"] = imagen_real  # Inyectamos la foto real con Python
    datos_finales["destacada"] = datos_dest
except Exception as e:
    print(f"⚠️ Error en destacada: {e}")

# Pausa de seguridad para evitar Error 429 de la API
time.sleep(12) 

# ==========================================
# 2. PROCESAR NOTICIAS SECUNDARIAS (5 Artículos)
# ==========================================
# Iteramos desde la noticia 1 hasta la 6 del RSS
for i in range(1, min(6, len(feed.entries))):
    noticia_sec = feed.entries[i]
    imagen_sec = obtener_imagen(noticia_sec)
    print(f"Procesando Secundaria {i}: {noticia_sec.title}")
    
    prompt_sec = f"""
    Resume esta noticia de videojuegos para una tarjeta web:
    Título: {noticia_sec.title}
    Devuelve UNICAMENTE un objeto JSON válido con esta estructura:
    {{
      "id": "sec-{i}",
      "categoria": "Actualidad",
      "titulo": "Título atractivo y conciso",
      "resumen": "Un resumen de máximo 3 líneas.",
      "enlace": "{noticia_sec.link}",
      "fecha": "{datetime.now().isoformat()}"
    }}
    """
    
    try:
        response_sec = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_sec,
            config=types.GenerateContentConfig(safety_settings=seguridad_permisiva, response_mime_type="application/json")
        )
        datos_sec = json.loads(response_sec.text)
        datos_sec["imagen"] = imagen_sec  # Inyectamos la foto real con Python
        datos_finales["secundarias"].append(datos_sec)
    except Exception as e:
        print(f"⚠️ Error en secundaria {i}: {e}")
        
    time.sleep(12) # Pausa de seguridad tras cada iteración

# Guardamos el archivo final estructurado
with open('noticias.json', 'w', encoding='utf-8') as f:
    json.dump(datos_finales, f, ensure_ascii=False, indent=2)

print("✅ noticias.json redactado y guardado correctamente con imágenes reales.")
