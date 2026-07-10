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

print("=== INICIANDO KAZOKUBOT: MOTOR GRÁFICO Y REDACTOR BLINDADO ===")

# 1. Configuración de APIs
api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")
pexels_key = os.environ.get("PEXELS_API_KEY")

if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    exit(1)

client = genai.Client(api_key=api_key)
archivo_articulos = "articulos.json"

# URLs limpias sin formato markdown
imagenes_respaldo = [
    "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200",
    "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1200",
    "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?q=80&w=1200",
    "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?q=80&w=1200",
    "https://images.unsplash.com/photo-1612287230202-1ff1d85d1e4e?q=80&w=1200"
]

def extraer_json_seguro(texto):
    """Extrae únicamente el JSON ignorando basura o Markdown alrededor."""
    match = re.search(r'\{.*\}', texto.strip(), re.DOTALL)
    return match.group(0) if match else texto.strip()

# Cargar base de datos
datos_web = {"articulos": []}
if os.path.exists(archivo_articulos):
    with open(archivo_articulos, "r", encoding="utf-8") as f:
        try: datos_web = json.load(f)
        except: pass

# =======================================================
# MÓDULO 1: ACTUALIZADOR DE IMÁGENES EXISTENTES
# =======================================================
actualizar_input = os.environ.get("INPUT_ACTUALIZAR", "")
if actualizar_input and actualizar_input.strip() and len(datos_web["articulos"]) > 0:
    comando_act = actualizar_input.strip().upper()
    print(f"\n🔄 MODO: ACTUALIZACIÓN DE IMÁGENES ACTIVADO ({comando_act})")
    
    titulos_a_actualizar = [t.strip().lower() for t in actualizar_input.split(";") if t.strip()]
    
    prompt_act = """
    Analiza el título de este artículo. Devuelve ÚNICAMENTE un JSON:
    {
      "es_videojuego": true/false,
      "prompt_imagen": "Si es videojuego, su nombre oficial. Si no lo es, escribe 1 o 2 palabras clave MUY PRECISAS en INGLÉS para buscar una fotografía profesional (ej: 'smartphone', 'processor', 'keyboard', 'esports')"
    }
    """
    
    for articulo in datos_web["articulos"]:
        if comando_act == "TODOS" or any(t in articulo["titulo"].lower() for t in titulos_a_actualizar):
            print(f"🖼️ Re-generando imagen para: '{articulo['titulo']}'...")
            try:
                res = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=f"Título: {articulo['titulo']}",
                    config=types.GenerateContentConfig(system_instruction=prompt_act, response_mime_type="application/json", temperature=0.2)
                )
                
                datos_img = json.loads(extraer_json_seguro(res.text))
                imagen_final = ""
                prompt_img = datos_img.get("prompt_imagen", "")
                
                if datos_img.get("es_videojuego") and rawg_key and prompt_img:
                    try:
                        req_r = requests.get(f"https://api.rawg.io/api/games?key={rawg_key}&search={urllib.parse.quote(prompt_img)}&page_size=1", timeout=10).json()
                        if req_r.get("results") and len(req_r["results"]) > 0:
                            imagen_final = req_r["results"][0].get("background_image", "")
                            print("🎮 Nueva imagen obtenida desde RAWG.")
                    except: pass
                
                if not imagen_final and pexels_key and prompt_img:
                    try:
                        req_p = requests.get(f"https://api.pexels.com/v1/search?query={urllib.parse.quote(prompt_img)}&per_page=5", headers={"Authorization": pexels_key}, timeout=10).json()
                        if req_p.get("photos") and len(req_p["photos"]) > 0:
                            imagen_final = random.choice(req_p["photos"])["src"]["landscape"]
                            print(f"📸 Nueva imagen obtenida desde Pexels ({prompt_img}).")
                    except: pass
                
                if not imagen_final:
                    imagen_final = random.choice(imagenes_respaldo)
                    print("🛡️ Nueva imagen obtenida del Respaldo.")
                
                articulo["imagen"] = imagen_final
                time.sleep(4) 
            except Exception as e:
                print(f"❌ Error al actualizar imagen: {e}")

# =======================================================
# MÓDULO 2: REDACCIÓN DE NUEVOS ARTÍCULOS
# =======================================================
temas_input = os.environ.get("INPUT_TEMAS", "")
temas_a_redactar = []

if temas_input and temas_input.strip():
    print("\n🛠️ MODO: CURACIÓN MANUAL (Nuevos artículos)")
    temas_a_redactar = [{"tema": t.strip(), "categoria": "Noticias"} for t in temas_input.split(";") if t.strip()]
elif actualizar_input and actualizar_input.strip():
    print("\n🛑 Piloto automático de redacción desactivado (Solo se actualizan imágenes).")
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
Tu estilo es profesional, analítico y táctico. Escribe un artículo optimizado para SEO.

REGLAS JSON (ESTRICTAS):
1. ÚNICAMENTE un objeto JSON.
2. En 'contenido', usa SIEMPRE comillas simples para atributos HTML.
3. 'es_videojuego': true si es de un juego específico, false si es hardware/tech.
4. 'prompt_imagen': Si es juego, el nombre oficial. Si es false, escribe 1 o 2 palabras clave precisas en INGLÉS para buscar fotos reales (ej. "keyboard", "ai robot", "server").

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
            print("🔄 Reintentando con servidor secundario...")
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Tema a redactar: {tema}",
                config=types.GenerateContentConfig(system_instruction=prompt_sistema, response_mime_type="application/json", temperature=0.7)
            )
            respuesta_texto = response.text
        
        # EXTRACTOR BLINDADO:
        texto_limpio = extraer_json_seguro(respuesta_texto)
        articulo_generado = json.loads(texto_limpio)
        
        imagen_final = ""
        prompt_img = articulo_generado.get("prompt_imagen", "")
        
        if articulo_generado.get("es_videojuego") and rawg_key and prompt_img:
            try:
                nombre_juego = urllib.parse.quote(prompt_img)
                r = requests.get(f"https://api.rawg.io/api/games?key={rawg_key}&search={nombre_juego}&page_size=1", timeout=10).json()
                if r.get("results") and len(r["results"]) > 0:
                    imagen_final = r["results"][0].get("background_image", "")
            except: pass
        
        if not imagen_final and pexels_key and prompt_img:
            try:
                query_pexels = urllib.parse.quote(prompt_img)
                headers = {"Authorization": pexels_key}
                r = requests.get(f"https://api.pexels.com/v1/search?query={query_pexels}&per_page=5", headers=headers, timeout=10).json()
                if r.get("photos") and len(r["photos"]) > 0:
                    foto_elegida = random.choice(r["photos"])
                    imagen_final = foto_elegida["src"]["landscape"]
            except: pass
        
        if not imagen_final:
            imagen_final = random.choice(imagenes_respaldo)
        
        articulo_final = {
            "id": id_articulo,
            "titulo": articulo_generado["titulo"],
            "slug": slug,
            "categoria": categoria,
            "tags": articulo_generado["tags"],
            "autor": "KazokuBot",
            "imagen": imagen_final,
            "fecha": time.strftime("%d %b, %Y"),
            "tiempo_lectura": articulo_generado["tiempo_lectura"],
            "meta_descripcion": articulo_generado["meta_descripcion"],
            "contenido": articulo_generado["contenido"]
        }
        
        datos_web["articulos"].insert(0, articulo_final)
        print(f"✅ ¡Artículo guardado exitosamente!")
        time.sleep(15)

    except Exception as e_total:
        print(f"❌ Error crítico: {e_total}")
        time.sleep(30)

# 7. Guardar en JSON
with open(archivo_articulos, "w", encoding="utf-8") as f:
    json.dump(datos_web, f, ensure_ascii=False, indent=2)

print("\n🚀 ¡PROCESO FINALIZADO!")
