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

print("=== INICIANDO KAZOKUBOT: REDACTOR EN JEFE IA (MOTOR DE IMÁGENES ESTABLE) ===")

# 1. Configuración de APIs
api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")
if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    exit(1)

client = genai.Client(api_key=api_key)
archivo_articulos = "articulos.json"

# 2. Banco de Imágenes de Respaldo Premium (100% Estables)
imagenes_respaldo = [
    "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200", # Setup Gaming
    "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1200", # Retro/Neon Gaming
    "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?q=80&w=1200", # Mando / Consola
    "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?q=80&w=1200", # Teclado PC RGB
    "https://images.unsplash.com/photo-1612287230202-1ff1d85d1e4e?q=80&w=1200", # Mando PS5
    "https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=1200", # Gafas VR
    "https://images.unsplash.com/photo-1552820728-8b83bb6b773f?q=80&w=1200", # Hardware / Placa Base
    "https://images.unsplash.com/photo-1600861194942-f884bfb03658?q=80&w=1200", # Neon Tech
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=1200", # Código / IA
    "https://images.unsplash.com/photo-1587202372634-32705e3bf49c?q=80&w=1200"  # Tarjeta Gráfica
]

# 3. Lógica Híbrida
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

# 4. Cargar base de datos
datos_web = {"articulos": []}
if os.path.exists(archivo_articulos):
    with open(archivo_articulos, "r", encoding="utf-8") as f:
        try:
            datos_web = json.load(f)
        except Exception as e:
            print(f"⚠️ Aviso: JSON previo no válido. Error: {e}")

# 5. El Prompt Maestro
prompt_sistema = """
Eres un periodista tecnológico y de videojuegos experto de 'KazokuGaming'.
Tu estilo es profesional, analítico, directo y con un tono táctico/entusiasta.
Escribe un artículo completo y optimizado para SEO.

REGLAS DE FORMATO JSON ULTRA-ESTRICTAS:
1. Devuelve ÚNICAMENTE un objeto JSON válido.
2. En el 'contenido', usa SIEMPRE comillas simples para los atributos HTML (ej. <p class='mb-4'>). NUNCA uses comillas dobles (") dentro del HTML.
3. 'es_videojuego': true si el tema principal es un videojuego específico, false si es tecnología o hardware.
4. 'prompt_imagen': Si es_videojuego es true, escribe SOLO el nombre oficial del juego en inglés (ej. "The Witcher 3"). Si es false, déjalo vacío "".

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

# 6. Bucle Principal
for item in temas_a_redactar:
    tema = item["tema"]
    categoria = item["categoria"]
    
    slug = re.sub(r'[^a-z0-9]+', '-', tema.lower()).strip('-')
    id_articulo = f"art-{slug}"[:50]
    
    if any(art["id"] == id_articulo for art in datos_web["articulos"]):
        print(f"⏭️ Saltando: '{tema}' (Ya existe).")
        continue

    print(f"\n✍️ Redactando artículo: {tema}...")
    
    try:
        respuesta_texto = ""
        try:
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
        
        # Sanitización de JSON
        texto_limpio = respuesta_texto.strip()
        if texto_limpio.startswith("```json"): texto_limpio = texto_limpio[7:]
        elif texto_limpio.startswith("```"): texto_limpio = texto_limpio[3:]
        if texto_limpio.endswith("```"): texto_limpio = texto_limpio[:-3]
        
        articulo_generado = json.loads(texto_limpio.strip())
        
        # --- NUEVO MOTOR DE IMÁGENES A PRUEBA DE FALLOS ---
        imagen_final = ""
        
        # 1. Intentar buscar la carátula oficial si es un videojuego
        if articulo_generado.get("es_videojuego") and rawg_key and articulo_generado.get("prompt_imagen"):
            try:
                nombre_juego = urllib.parse.quote(articulo_generado["prompt_imagen"])
                url_rawg = f"[https://api.rawg.io/api/games?key=](https://api.rawg.io/api/games?key=){rawg_key}&search={nombre_juego}&page_size=1"
                r = requests.get(url_rawg, timeout=10).json()
                if r.get("results") and len(r["results"]) > 0:
                    imagen_final = r["results"][0].get("background_image", "")
            except Exception as e:
                print(f"⚠️ RAWG no encontró la imagen: {e}")
        
        # 2. Si no es un juego, o RAWG falló, asignar una imagen premium aleatoria
        if not imagen_final:
            imagen_final = random.choice(imagenes_respaldo)
            print("📸 Asignando imagen premium de respaldo.")
        
        # --- ENSAMBLAJE ---
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
        print(f"❌ Error crítico al generar '{tema}': {e_total}")
        time.sleep(30)

# 7. Guardar en JSON
with open(archivo_articulos, "w", encoding="utf-8") as f:
    json.dump(datos_web, f, ensure_ascii=False, indent=2)

print("\n🚀 ¡PROCESO FINALIZADO! La base de datos está actualizada.")
