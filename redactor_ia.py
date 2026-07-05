import os
import json
import time
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: REDACTOR EN JEFE IA (SISTEMA BLINDADO) ===")

# 1. Configuración de APIs
api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")
if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    exit(1)

client = genai.Client(api_key=api_key)
archivo_articulos = "articulos.json"

# 2. Lógica Híbrida: Curación Manual vs. Piloto Automático
temas_input = os.environ.get("INPUT_TEMAS", "")
temas_a_redactar = []

if temas_input and temas_input.strip():
    print("🛠️ MODO: CURACIÓN MANUAL (Prioridad activada)")
    temas_a_redactar = [{"tema": t.strip(), "categoria": "Noticias"} for t in temas_input.split(";") if t.strip()]
else:
    print("🌍 MODO: PILOTO AUTOMÁTICO (Buscando tendencias de las últimas 24h...)")
    url_rss = "https://news.google.com/rss/search?q=videojuegos+OR+tecnologia+when:1d&hl=es&gl=ES&ceid=ES:es"
    try:
        req = urllib.request.Request(url_rss, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        for item in root.findall('.//item')[:3]:
            titulo_completo = item.find('title').text
            titulo_limpio = titulo_completo.rsplit(' - ', 1)[0]
            temas_a_redactar.append({"tema": titulo_limpio, "categoria": "Noticias"})
            print(f"📡 Tendencia detectada: {titulo_limpio}")
            
    except Exception as e:
        print(f"⚠️ Error al leer tendencias: {e}")
        temas_a_redactar = [{"tema": "Las innovaciones tecnológicas más esperadas en el gaming", "categoria": "Tecnología"}]

# 3. Cargar la base de datos existente
datos_web = {"articulos": []}
if os.path.exists(archivo_articulos):
    with open(archivo_articulos, "r", encoding="utf-8") as f:
        try:
            datos_web = json.load(f)
        except Exception as e:
            print(f"⚠️ Aviso: JSON previo no válido. Error: {e}")

# 4. El Prompt Maestro Ultra-Estricto
prompt_sistema = """
Eres un periodista tecnológico y de videojuegos experto de 'KazokuGaming'.
Tu estilo es profesional, analítico, directo y con un tono táctico/entusiasta.
Escribe un artículo completo y optimizado para SEO.

REGLAS DE FORMATO JSON ULTRA-ESTRICTAS (CRÍTICO):
1. Devuelve ÚNICAMENTE un objeto JSON válido. Cero texto fuera del JSON.
2. En el 'contenido' (que es HTML), DEBES usar SIEMPRE comillas simples para los atributos (ej. <p class='mb-4'>). NUNCA uses comillas dobles (") dentro del HTML porque romperás el formato JSON.
3. 'es_videojuego': true si el tema principal es un videojuego específico, false si es hardware o tecnología.
4. 'prompt_imagen': Si es_videojuego es true, escribe SOLO el nombre oficial del juego. Si es false, escribe una descripción corta en INGLÉS para la IA.

ESTRUCTURA JSON REQUERIDA:
{
  "titulo": "Título SEO atractivo pero profesional",
  "meta_descripcion": "Resumen de 150 caracteres para Google",
  "tags": ["Tag1", "Tag2"],
  "tiempo_lectura": "X min",
  "es_videojuego": true,
  "prompt_imagen": "texto",
  "contenido": "HTML aquí usando comillas simples para clases"
}
"""

# 5. Bucle de Redacción y Generación de Imágenes
for item in temas_a_redactar:
    tema = item["tema"]
    categoria = item["categoria"]
    
    slug = re.sub(r'[^a-z0-9]+', '-', tema.lower()).strip('-')
    id_articulo = f"art-{slug}"[:50]
    
    if any(art["id"] == id_articulo for art in datos_web["articulos"]):
        print(f"⏭️ Saltando: '{tema}' (El artículo ya fue publicado hoy).")
        continue

    print(f"\n✍️ Redactando artículo: {tema}...")
    
    try:
        respuesta_texto = ""
        # --- SISTEMA DE RESPALDO (FALLBACK) DE IA ---
        try:
            print("🧠 Intentando con servidor principal (3.5-flash)...")
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=f"Tema/Noticia a redactar: {tema}",
                config=types.GenerateContentConfig(
                    system_instruction=prompt_sistema,
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            respuesta_texto = response.text
        except Exception as e_principal:
            print(f"⚠️ Servidor principal falló: {e_principal}")
            print("🔄 Activando servidor de respaldo (2.5-flash)...")
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Tema/Noticia a redactar: {tema}",
                config=types.GenerateContentConfig(
                    system_instruction=prompt_sistema,
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            respuesta_texto = response.text
        
        # --- FILTRO DE LIMPIEZA (SANITIZACIÓN DE JSON) ---
        texto_limpio = respuesta_texto.strip()
        # Si la IA añade bloques de código Markdown por error, los eliminamos
        if texto_limpio.startswith("```json"):
            texto_limpio = texto_limpio[7:]
        elif texto_limpio.startswith("```"):
            texto_limpio = texto_limpio[3:]
        if texto_limpio.endswith("```"):
            texto_limpio = texto_limpio[:-3]
        texto_limpio = texto_limpio.strip()

        # Convertir texto a diccionario de Python
        articulo_generado = json.loads(texto_limpio)
        
        # --- MOTOR DUAL DE IMÁGENES ---
        imagen_final = ""
        
        if articulo_generado.get("es_videojuego") and rawg_key:
            try:
                nombre_juego = urllib.parse.quote(articulo_generado["prompt_imagen"])
                url_rawg = f"[https://api.rawg.io/api/games?key=](https://api.rawg.io/api/games?key=){rawg_key}&search={nombre_juego}&page_size=1"
                r = requests.get(url_rawg, timeout=10).json()
                if r.get("results") and len(r["results"]) > 0:
                    imagen_final = r["results"][0].get("background_image", "")
            except Exception as e:
                print(f"⚠️ RAWG no encontró la imagen: {e}")
        
        if not imagen_final:
            prompt_seguro = urllib.parse.quote(articulo_generado["prompt_imagen"] + ", highly detailed, 8k resolution, professional photography")
            imagen_final = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){prompt_seguro}?width=1200&height=720&nologo=true"
        
        # --- ENSAMBLAJE FINAL ---
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
        
        print("⏳ Pausa de enfriamiento (15s)...")
        time.sleep(15)

    except Exception as e_total:
        print(f"❌ Error crítico al generar '{tema}': {e_total}")
        time.sleep(30)

# 6. Guardar todo
with open(archivo_articulos, "w", encoding="utf-8") as f:
    json.dump(datos_web, f, ensure_ascii=False, indent=2)

print("\n🚀 ¡PROCESO FINALIZADO! La base de datos está actualizada.")
