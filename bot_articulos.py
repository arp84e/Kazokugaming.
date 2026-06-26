import os
import sys
import json
import re
import requests
import urllib.parse
import time
import random
import base64 # <- NUEVA LIBRERÍA: Necesaria para codificar y guardar las imágenes puras de Nano Banana
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

from ddgs import DDGS
from datetime import datetime

print("=== 🤖 KAZOKUBOT V5.0: MOTOR SEO ANTI-ERRORES Y GESTOR TOTAL ===")

# Captura de variables de entorno de GitHub
accion = os.environ.get("INPUT_ACCION", "1_generar_borrador")
tema = os.environ.get("INPUT_TEMA", "")
categoria = os.environ.get("INPUT_CATEGORIA", "Tecnología")
enlaces_manuales = os.environ.get("INPUT_ENLACES", "")
imagen_ok = os.environ.get("INPUT_IMAGEN_OK", "1")
palabras_clave_imagenes = os.environ.get("INPUT_PALABRAS_CLAVE_IMAGENES", "")
prompt_nano_banana = os.environ.get("INPUT_PROMPT_NANO_BANANA", "")
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
        print("🔗 2. Extrayendo datos de enlaces manuales...")
        for url in enlaces_manuales.split(","):
            url = url.strip()
            if not url: continue
            try:
                res_web = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                soup = BeautifulSoup(res_web.text, 'html.parser')
                for s in soup(["script", "style", "nav", "footer"]): s.decompose()
                contexto_enlaces_manuales += " ".join(soup.get_text().split())[:2500] + "\n\n"
            except: pass

    print("🧠 3. Solicitando redacción profesional a Gemini...")
    prompt = f"""
    Eres el redactor jefe de KazokuGaming. Escribe un artículo de prensa excepcional, profundo y 100% original sobre: '{tema}'.
    Usa esta info:
    {contexto_noticias_web}
    {contexto_enlaces_manuales}
    
    REGLA VITAL DE FORMATO PARA EL CUERPO: 
    - Devuelve HTML puro con <p>, <h2>, <h3>, <ul>, <li> y <strong>.
    - ESTÁ ESTRICTAMENTE PROHIBIDO usar estilos en línea. Todo debe ser limpio.
    - Devuelve un JSON con: 'titulo', 'resumen', 'cuerpo' y 'prompt_imagen'.
    - 'prompt_imagen': ACTÚA COMO DIRECTOR DE ARTE. Escribe un texto corto EN INGLÉS (máx 15 palabras) describiendo una imagen hiperrealista para ilustrar este artículo.
    """

    modelos_disponibles = ["gemini-3.5-flash", "gemini-3.5-pro", "gemini-3.0-flash", "gemini-2.5-flash"]
    exito_ia = False
    borrador_data = {}

    for modelo in modelos_disponibles:
        if exito_ia: break 
        print(f"\n🚀 Intentando contactar al servidor del modelo: [{modelo}]...")
        max_reintentos = 3 if modelo == "gemini-3.5-flash" else 2
        tiempo_espera = 15 if modelo == "gemini-3.5-flash" else 8 
        
        for intento in range(max_reintentos):
            try:
                print(f"   ⏳ Procesando con {modelo} (Intento {intento + 1}/{max_reintentos})...")
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                    config=types.GenerateContentConfig(safety_settings=seguridad, response_mime_type="application/json")
                )
                borrador_data = json.loads(response.text)
                borrador_data["categoria"] = categoria
                exito_ia = True
                print(f"   ✅ ¡Conexión exitosa usando el modelo {modelo}!")
                break 
            except Exception as e:
                print(f"   ⚠️ Fallo temporal con {modelo}: {e}")
                if intento < max_reintentos - 1:
                    print(f"   ⏳ Esperando {tiempo_espera}s antes de volver a intentar con este modelo...")
                    time.sleep(tiempo_espera)
                    tiempo_espera *= 1.5 

    if not exito_ia:
        print("\n❌ ERROR CRÍTICO: Todos los servidores modernos de Google están saturados en este momento. Inténtalo en 5 minutos.")
        sys.exit(1)

    try:
        termino_img = palabras_clave_imagenes if palabras_clave_imagenes.strip() else tema
        print(f"\n🖼️ 4. Procesando apartado visual...")
        
        imagenes_encontradas = []
        
        # --- NUEVO: INTEGRACIÓN NANO BANANA (Gemini Flash Image) ---
        if prompt_nano_banana.strip():
            print(f"   🍌 Solicitando a Nano Banana con tu prompt: '{prompt_nano_banana}'")
            try:
                img_response = client.models.generate_content(
                    model="gemini-3.1-flash-image", # Modelo de imagen optimizado
                    contents=[prompt_nano_banana],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio="16:9")
                    )
                )
                
                # Transformamos la imagen pura a Base64 temporalmente para incrustarla en el JSON
                for part in img_response.candidates[0].content.parts:
                    if part.inline_data:
                        img_bytes = part.inline_data.data
                        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                        mime_type = getattr(part.inline_data, "mime_type", "image/jpeg")
                        data_uri = f"data:{mime_type};base64,{img_b64}"
                        imagenes_encontradas.append(data_uri)
                        print("   ✅ ¡Imagen hiperrealista generada por Nano Banana y almacenada en memoria!")
                        break
            except Exception as e:
                print(f"   ⚠️ Fallo al usar Nano Banana, pasando a Plan B: {e}")

        prompt_ia_ingles = borrador_data.get("prompt_imagen", f"{termino_img} gaming high quality")
        
        # --- PLAN B DE RESPALDO (Si no se pidió Nano Banana o si falló) ---
        if not imagenes_encontradas:
            print(f"   🎨 Director de Arte IA sugiere usar red externa: '{prompt_ia_ingles}'")
            try:
                with DDGS() as ddgs:
                    query_ddgs = termino_img if "gam" in termino_img.lower() else f"{termino_img} gaming"
                    res_images = [r for r in ddgs.images(query_ddgs, max_results=10)]
                    for r in res_images:
                        img_url = r.get('image', '')
                        if img_url.startswith('http') and any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            imagenes_encontradas.append(img_url)
                        if len(imagenes_encontradas) >= 3: break
            except Exception as img_err:
                pass

        termino_url = urllib.parse.quote(prompt_ia_ingles + ", masterpiece, hyperrealistic")
        while len(imagenes_encontradas) < 10:
            semilla = random.randint(1, 9999999)
            imagenes_encontradas.append(f"https://image.pollinations.ai/prompt/{termino_url}?width=1200&height=675&nologo=true&seed={semilla}")

        borrador_data["imagenes_candidatas"] = imagenes_encontradas[:10]
        borrador_data["palabra_clave_usada"] = prompt_ia_ingles
        
        with open(archivo_borrador, "w", encoding="utf-8") as f:
            json.dump(borrador_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n🎉 ¡BORRADOR PREPARADO! Título: {borrador_data['titulo']}")
        print("="*80)
        print("🖼️ CATÁLOGO DE IMÁGENES PREPARADO")
        if prompt_nano_banana.strip():
            print(" 🔹 [1]: <Imagen renderizada nativamente por Nano Banana>")
        
    except Exception as e:
        print(f"❌ DETALLE TÉCNICO DEL ERROR FINAL: {e}")
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
    termino_img_fallback = urllib.parse.quote(borrador.get("palabra_clave_usada", "gaming") + ", masterpiece")
    
    imagenes_seleccionadas = []
    imagen_ok_limpio = str(imagen_ok).strip()
    
    if imagen_ok_limpio.lower() == "todas":
        imagenes_seleccionadas = candidatas
    else:
        indices = [int(x.strip()) - 1 for x in imagen_ok_limpio.split(",") if x.strip().isdigit()]
        for idx in indices:
            if 0 <= idx < len(candidatas): imagenes_seleccionadas.append(candidatas[idx])
                
    slug = re.sub(r'[^a-z0-9]+', '-', borrador["titulo"].lower()).strip('-')
    os.makedirs("articulos", exist_ok=True)
    rutas_imagenes_finales = []
    
    # --- SISTEMA INTELIGENTE DE EXTRACCIÓN DE IMÁGENES (Guarda localmente las Base64) ---
    for idx_img, img_data in enumerate(imagenes_seleccionadas):
        if img_data.startswith("data:image"):
            # ¡Es una imagen de Nano Banana! La decodificamos y la guardamos como archivo nativo .jpg
            header, encoded = img_data.split(",", 1)
            ext = header.split(";")[0].split("/")[1]
            if ext == "jpeg": ext = "jpg"
            
            sufijo = "" if idx_img == 0 else f"-{idx_img}"
            img_filename = f"img-{slug}{sufijo}.{ext}"
            img_path = f"articulos/{img_filename}"
            
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(encoded))
                
            rutas_imagenes_finales.append(f"articulos/{img_filename}")
            print(f"   📸 Nano Banana: Imagen convertida a archivo físico en '{img_path}'")
        else:
            rutas_imagenes_finales.append(img_data)
            
    if not rutas_imagenes_finales:
        rutas_imagenes_finales = [f"https://image.pollinations.ai/prompt/{termino_img_fallback}?width=1200&height=675&nologo=true&seed=1"]
        
    imagen_principal = rutas_imagenes_finales[0]
    
    nuevo = {
        "id": f"art-{slug}",
        "titulo": borrador["titulo"],
        "resumen": borrador["resumen"],
        "cuerpo": borrador["cuerpo"],
        "categoria": borrador["categoria"],
        "imagen": imagen_principal, # Se guarda la ruta relativa "articulos/img-X.jpg" para el grid principal
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

    html_filename = f"articulos/{slug}.html"
    palabras = len(re.sub('<[^<]+?>', '', nuevo["cuerpo"]).split())
    tiempo_lectura = max(1, round(palabras / 200))

    html_galeria = ""
    if len(rutas_imagenes_finales) > 1:
        html_galeria += f'''<div class="mt-12 pt-8 border-t border-slate-800/60"><h3 class="text-xs font-black text-cyan-400 uppercase tracking-widest mb-6 border-l-4 border-cyan-500 pl-3">Galería Multimedia</h3><div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">'''
        for i, img_sec in enumerate(rutas_imagenes_finales[1:]):
            fallback = f"https://image.pollinations.ai/prompt/{termino_img_fallback}%20extra%20{i}?width=1200&height=675&nologo=true&seed={i+100}"
            # Ajuste de ruta relativa si la imagen está guardada localmente
            img_sec_html = f"../{img_sec}" if not str(img_sec).startswith("http") else img_sec
            html_galeria += f'''<div class="rounded-2xl overflow-hidden border border-slate-800/50 shadow-md aspect-[16/10] bg-slate-950 group"><img src="{img_sec_html}" referrerpolicy="no-referrer" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" loading="lazy" onerror="this.src='{fallback}'"></div>'''
        html_galeria += '''</div></div>'''

    imagen_src_html = f"../{imagen_principal}" if not str(imagen_principal).startswith("http") else imagen_principal

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
            <img src="{imagen_src_html}" referrerpolicy="no-referrer" class="w-full h-full object-cover" onerror="this.src='https://image.pollinations.ai/prompt/{termino_img_fallback}?width=1200&height=675&nologo=true&seed=99'">
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
            if id_borrar.lower() in art["id"].lower() or id_borrar.lower() in art["titulo"].lower():
                slug = art["id"].replace("art-", "")
                ruta_html = f"articulos/{slug}.html"
                
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
