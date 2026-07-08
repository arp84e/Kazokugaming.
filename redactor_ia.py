import os
import json
import time
import re
import random
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: MOTOR GRÁFICO MULTI-BANCO ===")

# 1. Configuración de APIs
api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")
pexels_key = os.environ.get("PEXELS_API_KEY")

if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    exit(1)

client = genai.Client(api_key=api_key)
archivo_articulos = "articulos.json"

# 2. Banco de Imágenes de Respaldo Premium (Por si las APIs fallan)
imagenes_respaldo = [
    "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200",
    "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1200",
    "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?q=80&w=1200",
    "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?q=80&w=1200",
    "https://images.unsplash.com/photo-1612287230202-1ff1d85d1e4e?q=80&w=1200"
]

# 3. Lógica Híbrida: Manual vs Tendencias
temas_input = os.environ.get("INPUT_TEMAS", "")
temas_a_redactar = []

if temas_input and temas_input.strip():
    print("🛠️ MODO: CURACIÓN MANUAL")
    temas_a_redactar = [{"tema": t.strip(), "categoria": "Noticias"} for t in temas_input.split(";") if t.strip()]
else:
    print("🌍 MODO: PILOTO AUTOMÁTICO")
    url_rss = "https://news.google.com/rss/search?q=videojuegos+OR+tecnologia+when:1d&hl=es&gl=ES&ceid=ES:es"
    try:
        req = urllib.request.Request(url_rss, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        for item in root.findall('.//item')[:3]:
            titulo_limpio = item.find('title').text.rsplit(' - ', 1)[0]
            temas_a_redactar.append({"tema": titulo_limpio, "categoria": "Noticias"})
            print(f"📡 Tendencia: {titulo_limpio}")
    except Exception as e:
        print(f"⚠️ Error al leer tendencias: {e}")
        temas_a_redactar = [{"tema": "Avances en inteligencia artificial en 2026", "categoria": "Tecnología"}]

# 4. Cargar base de datos
datos_web = {"articulos": []}
if os.path.exists(archivo_articulos):
    with open(archivo_articulos, "r", encoding="utf-8") as f:
        try: datos_web = json.load(f)
        except: pass

# 5. El Prompt Maestro
prompt_sistema = """
Eres un periodista tecnológico y de videojuegos experto de 'KazokuGaming'.
Tu estilo es profesional, analítico y táctico. Escribe un artículo optimizado para SEO.

REGLAS JSON:
1. ÚNICAMENTE un objeto JSON.
2. En 'contenido', usa SIEMPRE comillas simples para atributos HTML (ej. <p class='mb-4'>).
3. 'es_videojuego': true si es de un juego específico, false si es hardware/tech.
4. 'prompt_imagen': Si es juego, el nombre oficial. Si es false, escribe 2 palabras clave en INGLÉS para buscar en un banco de imágenes (ej. "gaming pc", "artificial intelligence", "smartphone").

ESTRUCTURA JSON:
{
  "titulo": "Título SEO",
  "meta_descripcion": "Resumen 150 caracteres",
  "tags": ["Tag1", "Tag2"],
  "tiempo_lectura": "X min",
  "es_videojuego": true,
  "prompt_imagen": "texto",
  "contenido": "HTML aquí usando comillas simples"
}
"""

# 6. Bucle Principal
for item in temas_a_redactar:
    tema = item["tema"]
    categoria = item["categoria"]
    slug = re.sub(r'[^a-z0-9]+', '-', tema.lower()).strip('-')
    id_articulo = f"art-{slug}"[:50]
    
    if any(art["id"] == id_articulo for art in datos_web["articulos"]):
        print(f"⏭️ Saltando: '{tema}' (Ya existe).")
        continue

    print(f"\n✍️ Redactando: {tema}...")
    
    try:
        respuesta_texto = ""
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=f"Tema a redactar: {tema}",
                config=types.GenerateContentConfig(system_instruction=prompt_sistema, response_mime_type="application/json", temperature=0.7)
            )
            respuesta_texto = response.text
        except Exception:
            print("🔄 Activando respaldo IA (2.5-flash)...")
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Tema a redactar: {tema}",
                config=types.GenerateContentConfig(system_instruction=prompt_sistema, response_mime_type="application/json", temperature=0.7)
            )
            respuesta_texto = response.text
        
        texto_limpio = respuesta_texto.strip()
        if texto_limpio.startswith("
http://googleusercontent.com/immersive_entry_chip/0
http://googleusercontent.com/immersive_entry_chip/1
http://googleusercontent.com/immersive_entry_chip/2

Guarda los cambios, crea tu clave gratuita de Pexels, súbela a GitHub y ejecuta el bot. A partir de ahora, tus artículos se ilustrarán automáticamente con fotografías espectaculares, libres de derechos de autor y elegidas dinámicamente según el tema de la noticia.
