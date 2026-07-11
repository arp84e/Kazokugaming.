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

print("=== INICIANDO KAZOKUBOT: MOTOR GRÁFICO Y REDACTOR BLINDADO (V2) ===")

# 1. Configuración de APIs
api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")
pexels_key = os.environ.get("PEXELS_API_KEY")

if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    exit(1)

client = genai.Client(api_key=api_key)
archivo_articulos = "articulos.json"

imagenes_respaldo = [
    "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200",
    "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1200",
    "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?q=80&w=1200"
]

def extraer_json_seguro(texto):
    match = re.search(r'\{.*\}', texto.strip(), re.DOTALL)
    return match.group(0) if match else texto.strip()

# Cargar base de datos
datos_web = {"articulos": []}
if os.path.exists(archivo_articulos):
    with open(archivo_articulos, "r", encoding="utf-8") as f:
        try: datos_web = json.load(f)
        except: pass

# =======================================================
# MÓDULO REDACCIÓN DE NUEVOS ARTÍCULOS CON SEO Y OPENGRAPH
# =======================================================
temas_input = os.environ.get("INPUT_TEMAS", "")
temas_a_redactar = []

if temas_input and temas_input.strip():
    print("\n🛠️ MODO: CURACIÓN MANUAL (Nuevos artículos)")
    temas_a_redactar = [{"tema": t.strip(), "categoria": "Noticias"} for t in temas_input.split(";") if t.strip()]
else:
    print("\n🌍 MODO: PILOTO AUTOMÁTICO (Buscando tendencias...)")
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

prompt_sistema = """
Eres un periodista tecnológico y de videojuegos experto de 'KazokuGaming'.
Tu estilo es profesional, analítico y táctico. Escribe un artículo muy completo.

REGLAS JSON (ESTRICTAS):
1. ÚNICAMENTE un objeto JSON.
2. En 'contenido', usa SIEMPRE comillas simples para atributos HTML.
3. 'es_videojuego': true si es de un juego específico, false si es hardware/tech.
4. 'prompt_imagen': Si es juego, el nombre oficial. Si es false, 1 o 2 palabras clave en INGLÉS para fotos reales (ej. "keyboard").
5. 'seo': Incluye keywords clave separadas por comas.
6. 'open_graph': Crea un título y descripción impactantes optimizados para compartir en redes sociales.
7. 'articulos_relacionados': Inventa 2 slugs semánticamente probables que tengan relación con el tema.

ESTRUCTURA JSON OBLIGATORIA:
{
  "titulo": "Título principal del post",
  "meta_descripcion": "Resumen 150 caracteres",
  "tags": ["Tag1", "Tag2"],
  "tiempo_lectura": "X min",
  "es_videojuego": true,
  "prompt_imagen": "texto",
  "contenido": "HTML completo aquí usando comillas simples",
  "seo": {
    "keywords": "palabra1, palabra2, palabra3"
  },
  "open_graph": {
    "og_title": "Título corto y viral para Twitter/Discord",
    "og_description": "Descripción gancho para redes sociales",
    "og_type": "article"
  },
  "articulos_relacionados": ["slug-de-ejemplo-1", "slug-de-ejemplo-2"]
}
"""

for item in temas_a_redactar:
    tema = item["tema"]
    categoria = item["categoria"]
    slug = re.sub(r'[^a-z0-9]+', '-', tema.lower()).strip('-')
    id_articulo = f"art-{slug}"[:50]
    
    if any(art["id"] == id_articulo for art in datos_web["articulos"]):
        print(f"⏭️ Saltando: '{tema}' (Ya existe).")
        continue

    print(f"\n✍️ Redactando (SEO Avanzado): {tema}...")
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=f"Tema a redactar: {tema}",
            config=types.GenerateContentConfig(system_instruction=prompt_sistema, response_mime_type="application/json", temperature=0.7)
        )
        
        texto_limpio = extraer_json_seguro(response.text)
        articulo_generado = json.loads(texto_limpio)
        
        imagen_final = ""
        prompt_img = articulo_generado.get("prompt_imagen", "")
        
        if articulo_generado.get("es_videojuego") and rawg_key and prompt_img:
            try:
                r = requests.get(f"https://api.rawg.io/api/games?key={rawg_key}&search={urllib.parse.quote(prompt_img)}&page_size=1", timeout=10).json()
                if r.get("results"): imagen_final = r["results"][0].get("background_image", "")
            except: pass
        
        if not imagen_final and pexels_key and prompt_img:
            try:
                r = requests.get(f"https://api.pexels.com/v1/search?query={urllib.parse.quote(prompt_img)}&per_page=5", headers={"Authorization": pexels_key}, timeout=10).json()
                if r.get("photos"): imagen_final = random.choice(r["photos"])["src"]["landscape"]
            except: pass
        
        if not imagen_final: imagen_final = random.choice(imagenes_respaldo)
        
        # NUEVA ESTRUCTURA COMPLETA
        articulo_final = {
            "id": id_articulo,
            "titulo": articulo_generado["titulo"],
            "slug": slug,
            "categoria": categoria,
            "tags": articulo_generado.get("tags", []),
            "autor": "KazokuBot",
            "imagen": imagen_final,
            "fecha": time.strftime("%d %b, %Y"),
            "tiempo_lectura": articulo_generado.get("tiempo_lectura", "3 min"),
            "contenido": articulo_generado["contenido"],
            "meta_descripcion": articulo_generado["meta_descripcion"],
            "seo": articulo_generado.get("seo", {"keywords": "gaming, videojuegos, pc, noticias"}),
            "open_graph": articulo_generado.get("open_graph", {"og_title": articulo_generado["titulo"], "og_description": articulo_generado["meta_descripcion"], "og_type": "article"}),
            "articulos_relacionados": articulo_generado.get("articulos_relacionados", [])
        }
        
        datos_web["articulos"].insert(0, articulo_final)
        print(f"✅ ¡Artículo guardado exitosamente!")
        time.sleep(15)

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        time.sleep(15)

with open(archivo_articulos, "w", encoding="utf-8") as f:
    json.dump(datos_web, f, ensure_ascii=False, indent=2)

print("\n🚀 ¡PROCESO FINALIZADO!")
