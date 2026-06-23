import os
import sys
import json
import re
import requests
import urllib.parse
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from duckduckgo_search import DDGS
from datetime import datetime

print("=== 🤖 KAZOKUBOT V5.0: MOTOR SEO ANTI-ERRORES Y GESTOR TOTAL ===")

# Captura de variables de entorno de GitHub
accion = os.environ.get("INPUT_ACCION", "1_generar_borrador")
tema = os.environ.get("INPUT_TEMA", "")
categoria = os.environ.get("INPUT_CATEGORIA", "Tecnología")
enlaces_manuales = os.environ.get("INPUT_ENLACES", "")
imagen_ok = os.environ.get("INPUT_IMAGEN_OK", "1")
palabras_clave_imagenes = os.environ.get("INPUT_PALABRAS_CLAVE_IMAGENES", "")
id_borrar = os.environ.get("INPUT_ID_BORRAR", "")
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: No se configuró GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client(api_key=api_key)
archivo_borrador = "articulos_borrador.json"
archivo_oficial = "articulos.json"

seguridad = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

# ==========================================================
# ACCIÓN 1: GENERAR BORRADOR
# ==========================================================
if accion == "1_generar_borrador":
    if not tema:
        print("❌ ERROR: Debes especificar un tema para el artículo.")
        sys.exit(1)

    contexto_noticias_web = ""
    print(f"🔍 1. Investigando en la red sobre: '{tema}'...")
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(tema, max_results=6):
                contexto_noticias_web += f"Fuente: {r['title']}\nDatos: {r['body']}\n\n"
    except Exception as e:
        print(f"⚠️ Alerta DDGS: {e}")

    contexto_enlaces_manuales = ""
    if enlaces_manuales:
        enlaces_lista = [url.strip() for url in enlaces_manuales.split(",") if url.strip()]
        print(f"🔗 2. Procesando {len(enlaces_lista)} enlaces manuales individualmente...")
        
        for index, url in enumerate(enlaces_lista, 1):
            try:
                # 2.1 Extraer texto de la web
                res_web = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                soup = BeautifulSoup(res_web.text, 'html.parser')
                for s in soup(["script", "style", "nav", "footer", "header", "aside"]): s.decompose()
                texto_crudo = " ".join(soup.get_text().split())[:3000] # Tomamos un poco más de contexto
                
                # 2.2 Crear un mini-borrador por cada enlace usando Gemini
                print(f"   🧠 Generando Análisis Previo {index}/{len(enlaces_lista)}...")
                prompt_mini = f"Resume y extrae los puntos más importantes, datos técnicos y citas clave del siguiente texto extraído de una web. Establécelo como 'Análisis {index}':\n\n{texto_crudo}"
                
                res_mini = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt_mini,
                    config=types.GenerateContentConfig(safety_settings=seguridad)
                )
                
                # 2.3 Acumular los análisis estructurados
                contexto_enlaces_manuales += f"--- ANÁLISIS DEL ENLACE {index} ---\n{res_mini.text}\n\n"
                
            except Exception as e:
                print(f"   ⚠️ Error procesando enlace {index} ({url}): {e}")

    print("🧠 3. Solicitando redacción profesional a Gemini...")
    prompt = f"""
    Eres el redactor jefe de KazokuGaming. Escribe un artículo de prensa excepcional, profundo y 100% original sobre: '{tema}'.
    Usa esta info:
    {contexto_noticias_web}
    {contexto_enlaces_manuales}
    
    REGLA VITAL DE FORMATO PARA EL CUERPO: 
    - Devuelve HTML puro con <p>, <h2>, <h3>, <ul>, <li> y <strong>.
    - ESTÁ ESTRICTAMENTE PROHIBIDO usar estilos en línea (NO uses 'style=', NO uses colores). Todo debe ser limpio para que el CSS de la web tome el control.
    - Devuelve un JSON con: 'titulo', 'resumen' y 'cuerpo'.
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(safety_settings=seguridad, response_mime_type="application/json")
        )
        borrador_data = json.loads(response.text)
        borrador_data["categoria"] = categoria
        
        # 🖼️ BÚSQUEDA AVANZADA DE IMÁGENES
        termino_img = palabras_clave_imagenes if palabras_clave_imagenes.strip() else tema
        print(f"🖼️ 4. Buscando imágenes precisas para: '{termino_img}'...")
        
        imagenes_encontradas = []
        try:
            with DDGS() as ddgs:
                # Quitamos el filtro 'license' para asegurar resultados precisos a la palabra clave
                res_images = [r for r in ddgs.images(termino_img, max_results=30)]
                for r in res_images:
                    if r.get('image') and r.get('image').startswith('http'):
                        imagenes_encontradas.append(r.get('image'))
                    if len(imagenes_encontradas) >= 10: break
        except Exception as img_err:
            print(f"⚠️ Error al buscar imágenes: {img_err}")

        # Auto-sanación con IA Generativa si no encuentra suficientes
        termino_url = urllib.parse.quote(termino_img)
        while len(imagenes_encontradas) < 10:
            random_id = len(imagenes_encontradas) + 1
            # Pollinations genera imágenes libres de copyright basadas en la palabra clave al vuelo!
            imagenes_encontradas.append(f"https://image.pollinations.ai/prompt/{termino_url}%20gaming%20wallpaper%20high%20quality%20{random_id}?width=1200&height=675&nologo=true")

        borrador_data["imagenes_candidatas"] = imagenes_encontradas[:10]
        borrador_data["palabra_clave_usada"] = termino_img # Guardamos la palabra clave para la auto-sanación HTML
        
        with open(archivo_borrador, "w", encoding="utf-8") as f:
            json.dump(borrador_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n🎉 ¡BORRADOR PREPARADO! Título: {borrador_data['titulo']}")
        print("="*80)
        print(f"🖼️ CATÁLOGO DE 10 IMÁGENES ENCONTRADAS PARA '{termino_img}':")
        for idx, url in enumerate(borrador_data["imagenes_candidatas"], 1):
            print(f" 🔹 [{idx}]: {url}")
        print("="*80)
        
    except Exception as e:
        print(f"❌ ERROR EN BORRADOR: {e}")
        sys.exit(1)

# ==========================================================
# ACCIÓN 2: PUBLICAR BORRADOR
# ==========================================================
elif accion == "2_publicar_borrador":
    if not os.path.exists(archivo_borrador):
        print("❌ ERROR: No hay borrador para publicar.")
        sys.exit(1)
        
    with open(archivo_borrador, "r", encoding="utf-8") as f:
        borrador = json.load(f)
        
    candidatas = borrador.get("imagenes_candidatas", [])
    termino_img_fallback = urllib.parse.quote(borrador.get("palabra_clave_usada", "gaming"))
    
    imagenes_seleccionadas = []
    imagen_ok_limpio = str(imagen_ok).strip()
    
    if imagen_ok_limpio.lower() == "todas":
        imagenes_seleccionadas = candidatas
    else:
        indices = [int(x.strip()) - 1 for x in imagen_ok_limpio.split(",") if x.strip().isdigit()]
        for idx in indices:
            if 0 <= idx < len(candidatas): imagenes_seleccionadas.append(candidatas[idx])
                
    if not imagenes_seleccionadas:
        imagenes_seleccionadas = [candidatas[0]] if candidatas else [f"https://image.pollinations.ai/prompt/{termino_img_fallback}?width=1200&height=675&nologo=true"]
        
    imagen_principal = imagenes_seleccionadas[0]
    slug = re.sub(r'[^a-z0-9]+', '-', borrador["titulo"].lower()).strip('-')
    
    nuevo = {
        "id": f"art-{slug}",
        "titulo": borrador["titulo"],
        "resumen": borrador["resumen"],
        "cuerpo": borrador["cuerpo"],
        "categoria": borrador["categoria"],
        "imagen": imagen_principal,
        "fecha": datetime.now().strftime("%d %b, %Y")
    }
    
    lista = []
    if os.path.exists(archivo_oficial):
        with open(archivo_oficial, "r", encoding="utf-8") as f:
            try:
                lista = json.load(f)
                if isinstance(lista, dict): lista = lista.get("articulos", [])
            except: pass
            
    lista.insert(0, nuevo)
    with open(archivo_oficial, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

    os.makedirs("articulos", exist_ok=True)
    html_filename = f"articulos/{slug}.html"
    
    palabras = len(re.sub('<[^<]+?>', '', nuevo["cuerpo"]).split())
    tiempo_lectura = max(1, round(palabras / 200))

    html_galeria = ""
    if len(imagenes_seleccionadas) > 1:
        html_galeria += '''<div class="mt-12 pt-8 border-t border-slate-800/60"><h3 class="text-xs font-black text-cyan-400 uppercase tracking-widest mb-6 border-l-4 border-cyan-500 pl-3">Galería Multimedia</h3><div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">'''
        for i, img_sec in enumerate(imagenes_seleccionadas[1:]):
            fallback = f"https://image.pollinations.ai/prompt/{termino_img_fallback}%20extra%20{i}?width=1200&height=675&nologo=true"
            # referrerpolicy="no-referrer" evita que las webs bloqueen la imagen. onerror hace que si falla, cargue una imagen IA de respaldo.
            html_galeria += f'''<div class="rounded-2xl overflow-hidden border border-slate-800/50 shadow-md aspect-[16/10] bg-slate-950 group"><img src="{img_sec}" referrerpolicy="no-referrer" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" loading="lazy" onerror="this.src='{fallback}'"></div>'''
        html_galeria += '''</div></div>'''

    # CSS forzado con !important para garantizar contraste perfecto y legibilidad anulando la IA
    plantilla_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{nuevo["titulo"]} | KazokuGaming</title>
    <link rel="icon" type="image/png" href="../favicon.png">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0b0f19; }}
        /* Forzador absoluto de legibilidad */
        .prose-custom * {{ color: #cbd5e1 !important; background-color: transparent !important; font-family: inherit !important; line-height: 1.8 !important; }}
        .prose-custom h2, .prose-custom h3 {{ color: #f8fafc !important; font-weight: 800 !important; margin-top: 2em !important; margin-bottom: 1em !important; border-left: 4px solid #06b6d4; padding-left: 12px; }}
        .prose-custom strong, .prose-custom b {{ color: #22d3ee !important; font-weight: 700 !important; }}
        .prose-custom p {{ margin-bottom: 1.5em !important; font-size: 1.125rem !important; }}
        .prose-custom ul {{ list-style-type: disc !important; margin-left: 1.5em !important; margin-bottom: 1.5em !important; }}
    </style>
</head>
<body class="text-slate-200 min-h-screen flex flex-col justify-between">
    <div id="header-container"></div>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex-grow w-full">
        <div class="mb-8">
            <span class="text-xs bg-cyan-900/30 text-cyan-400 px-3 py-1 rounded border border-cyan-800/50 uppercase font-bold tracking-widest">{nuevo["categoria"]}</span>
            <span class="text-slate-500 text-xs ml-3 border-l border-slate-700 pl-3">⏳ {tiempo_lectura} min de lectura</span>
            <h1 class="text-4xl sm:text-5xl font-extrabold text-white mt-4 mb-4 leading-tight">{nuevo["titulo"]}</h1>
            <p class="text-lg text-slate-400">{nuevo["resumen"]}</p>
        </div>
        <div class="w-full aspect-video rounded-3xl overflow-hidden mb-10 shadow-2xl border border-slate-800/50 bg-slate-900">
            <img src="{nuevo["imagen"]}" referrerpolicy="no-referrer" class="w-full h-full object-cover" onerror="this.src='https://image.pollinations.ai/prompt/{termino_img_fallback}?width=1200&height=675&nologo=true'">
        </div>
        <div class="prose-custom bg-slate-900/40 p-8 sm:p-10 rounded-3xl border border-slate-700/50 shadow-lg">
            {nuevo["cuerpo"]}
        </div>
        {html_galeria}
    </main>
    <script src="../header.js"></script>
</body>
</html>'''

    with open(html_filename, "w", encoding="utf-8") as hf:
        hf.write(plantilla_html)
        
    os.remove(archivo_borrador)
    print(f"🚀 ¡PUBLICACIÓN GLOBAL EMITIDA! Artículo legible y estático creado en: {html_filename}")

# ==========================================================
# ACCIÓN 3: ELIMINAR ARTÍCULO
# ==========================================================
elif accion == "3_eliminar_articulo":
    if not id_borrar:
        print("❌ ERROR: Para eliminar, debes escribir el ID o título del artículo.")
        sys.exit(1)
        
    if os.path.exists(archivo_oficial):
        with open(archivo_oficial, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                lista = data if isinstance(data, list) else data.get("articulos", [])
            except:
                lista = []
                
        nueva_lista = []
        eliminados = 0
        
        for art in lista:
            # Busca coincidencia parcial en el ID o en el Título ignorando mayúsculas
            if id_borrar.lower() in art["id"].lower() or id_borrar.lower() in art["titulo"].lower():
                slug = art["id"].replace("art-", "")
                ruta_html = f"articulos/{slug}.html"
                
                # Borrar el archivo HTML estático si existe
                if os.path.exists(ruta_html):
                    os.remove(ruta_html)
                    print(f"🗑️ Archivo HTML destruido: {ruta_html}")
                    
                print(f"🗑️ Artículo eliminado de la base de datos: {art['titulo']}")
                eliminados += 1
            else:
                nueva_lista.append(art)
                
        if eliminados > 0:
            with open(archivo_oficial, "w", encoding="utf-8") as f:
                json.dump(nueva_lista, f, ensure_ascii=False, indent=2)
            print(f"✅ Proceso terminado. Se eliminaron {eliminados} artículo(s).")
        else:
            print(f"⚠️ No se encontró ningún artículo que coincida con '{id_borrar}'.")
            sys.exit(1)
    else:
        print("⚠️ No existe la base de datos de artículos.")
