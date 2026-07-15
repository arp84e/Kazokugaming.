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

print("=== INICIANDO KAZOKUBOT: MOTOR PERIODÍSTICO (SISTEMA MULTI-MODELO) ===")

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
    texto = texto.strip()
    match = re.search(r'\{.*\}', texto, re.DOTALL)
    return match.group(0) if match else texto

def generar_con_reintentos(prompt_texto, config_ia, max_intentos=3):
    modelos_disponibles = ['gemini-3.5-flash', 'gemini-2.5-flash']
    for intento in range(max_intentos):
        for modelo in modelos_disponibles:
            try: return client.models.generate_content(model=modelo, contents=prompt_texto, config=config_ia)
            except Exception as e:
                error_str = str(e).lower()
                if "503" in error_str or "unavailable" in error_str or "429" in error_str:
                    print(f"⚠️ Modelo {modelo} saturado. Cambiando...")
                    continue
                else: raise e 
        espera = 10
        print(f"⚠️ Nodos ocupados. Reintentando en {espera}s... ({intento+1}/{max_intentos})")
        time.sleep(espera)
    raise Exception("❌ Servidores inactivos.")

datos_web = {"articulos": []}
if os.path.exists(archivo_articulos):
    with open(archivo_articulos, "r", encoding="utf-8") as f:
        try: datos_web = json.load(f)
        except: pass

temas_input = os.environ.get("INPUT_TEMAS", "")
temas_a_redactar = []

if temas_input and temas_input.strip():
    print("\n🛠️ MODO MANUAL")
    temas_a_redactar = [{"tema": t.strip(), "categoria": "Noticias"} for t in temas_input.split(";") if t.strip()]
else:
    print("\n🌍 MODO PILOTO AUTOMÁTICO (Buscando titulares RSS...)")
    url_rss = "https://news.google.com/rss/search?q=videojuegos+OR+hardware+when:1d&hl=es&gl=ES&ceid=ES:es"
    try:
        req = urllib.request.Request(url_rss, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        for item in root.findall('.//item')[:3]:
            titulo_limpio = item.find('title').text.rsplit(' - ', 1)[0]
            temas_a_redactar.append({"tema": titulo_limpio, "categoria": "Noticias"})
            print(f"📡 Noticia detectada: {titulo_limpio}")
    except Exception as e:
        print(f"⚠️ Error al leer RSS: {e}")

prompt_sistema = """
Eres un periodista tecnológico de 'KazokuGaming'. Redacta una noticia completa.
Devuelve ÚNICAMENTE un objeto JSON. Usa comillas simples para atributos HTML en 'contenido'.
ESTRUCTURA:
{
  "titulo": "Título de la Noticia",
  "meta_descripcion": "Resumen 150 caracteres",
  "tags": ["Tag1", "Tag2"],
  "tiempo_lectura": "3 min",
  "es_videojuego": true,
  "prompt_imagen": "texto de busqueda en ingles",
  "contenido": "<p>Cuerpo de la noticia...</p>",
  "seo": { "keywords": "palabras clave" },
  "open_graph": { "og_title": "Título", "og_description": "Gancho", "og_type": "article" },
  "articulos_relacionados": []
}
"""

for item in temas_a_redactar:
    tema = item["tema"]
    categoria = item["categoria"]
    slug = re.sub(r'[^a-z0-9]+', '-', tema.lower()).strip('-')
    id_articulo = f"art-{slug}"[:50]
    
    if any(art.get("id") == id_articulo for art in datos_web.get("articulos", [])):
        print(f"⏭️ Saltando: '{tema}' (Ya redactado).")
        continue

    print(f"\n✍️ Redactando: {tema}...")
    try:
        # CORRECCIÓN: Sin response_mime_type
        config_redactor = types.GenerateContentConfig(system_instruction=prompt_sistema, temperature=0.7, tools=[{"google_search": {}}])
        response = generar_con_reintentos(f"Tema a investigar y redactar: {tema}", config_redactor)
        
        articulo_generado = json.loads(extraer_json_seguro(response.text))
        
        imagen_final = ""
        prompt_img = articulo_generado.get("prompt_imagen", "")
        
        if articulo_generado.get("es_videojuego") and rawg_key and prompt_img:
            try:
                r = requests.get(f"https://api.rawg.io/api/games?key={rawg_key}&search={urllib.parse.quote(prompt_img)}&page_size=1", timeout=5).json()
                if r.get("results"): imagen_final = r["results"][0].get("background_image", "")
            except: pass
        
        if not imagen_final and pexels_key and prompt_img:
            try:
                r = requests.get(f"https://api.pexels.com/v1/search?query={urllib.parse.quote(prompt_img)}&per_page=5", headers={"Authorization": pexels_key}, timeout=5).json()
                if r.get("photos"): imagen_final = random.choice(r["photos"])["src"]["landscape"]
            except: pass
        
        if not imagen_final: 
            imagen_final = random.choice(imagenes_respaldo)
        
        articulo_final = {
            "id": id_articulo,
            "titulo": articulo_generado.get("titulo", tema),
            "slug": slug,
            "categoria": categoria,
            "tags": articulo_generado.get("tags", []),
            "autor": "KazokuBot",
            "imagen": imagen_final,
            "fecha": time.strftime("%d %b, %Y"),
            "tiempo_lectura": articulo_generado.get("tiempo_lectura", "3 min"),
            "contenido": articulo_generado.get("contenido", "<p>Error de procesamiento...</p>"),
            "meta_descripcion": articulo_generado.get("meta_descripcion", "")
        }
        
        datos_web["articulos"].insert(0, articulo_final)
        print(f"✅ ¡Noticia guardada!")
        
        with open(archivo_articulos, "w", encoding="utf-8") as f:
            json.dump(datos_web, f, ensure_ascii=False, indent=2)
            
        time.sleep(5)

    except Exception as e:
        print(f"❌ Error al procesar noticia: {e}")

print("\n🚀 ¡PROCESO FINALIZADO!")
