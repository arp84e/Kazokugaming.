import os
import sys
import json
import re
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from duckduckgo_search import DDGS

print("=== 🤖 KAZOKUBOT V3: MEGA MOTOR EDITORIAL ===")

accion = os.environ.get("INPUT_ACCION", "1_generar_borrador")
tema = os.environ.get("INPUT_TEMA", "")
categoria = os.environ.get("INPUT_CATEGORIA", "Tecnología")
enlaces_manuales = os.environ.get("INPUT_ENLACES", "")
imagen_ok = os.environ.get("INPUT_IMAGEN_OK", "1")
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

def extraer_imagenes_de_enlaces(texto_enlaces):
    imagenes_encontradas = []
    if not texto_enlaces:
        return imagenes_encontradas
        
    urls = [u.strip() for u in texto_enlaces.split(",") if u.strip().startswith("http")]
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                og_meta = soup.find("meta", attrs={"property": "og:image"}) or soup.find("meta", attrs={"name": "twitter:image"})
                if og_meta and og_meta.get("content"):
                    img_url = og_meta["content"].strip()
                    if img_url.startswith("http") and img_url not in imagenes_encontradas:
                        imagenes_encontradas.append(img_url)
                
                for img_tag in soup.find_all("img"):
                    src = img_tag.get("src") or img_tag.get("data-src")
                    if src and src.startswith("http") and not any(x in src.lower() for x in ["icon", "logo", "avatar", "sprite"]):
                        if src not in imagenes_encontradas:
                            imagenes_encontradas.append(src)
                    if len(imagenes_encontradas) >= 4:
                        break
        except Exception:
            pass
    return imagenes_encontradas

if accion == "1_generar_borrador":
    if not tema:
        print("❌ ERROR: Falta el tema.")
        sys.exit(1)
        
    contexto_busqueda = ""
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(f"{tema} gaming technology", max_results=3))
            for res in resultados:
                contexto_busqueda += f"- {res['title']}: {res['body']} (Fuente: {res['href']})\n"
    except Exception:
        pass

    if enlaces_manuales:
        contexto_busqueda += f"\n[ENLACES OFICIALES]:\n{enlaces_manuales}\n"

    print("✍️ Fase 2: Redactando MEGA ARTÍCULO con Gemini...")
    prompt = f"""
    Actúa como un Redactor Jefe Senior y Experto Analista para KazokuGaming. Crea un mega-artículo técnico, profundo y espectacular:
    
    TEMA: {tema}
    CATEGORÍA: {categoria}
    INVESTIGACIÓN: {contexto_busqueda}
    
    INSTRUCCIONES DE REDACCIÓN Y FORMATO WEB:
    1. TÍTULO: Profesional, magnético y optimizado SEO (Max 70 caracteres).
    2. RESUMEN: Gancho corto de 2 líneas.
    3. CUERPO (HTML LIMPIO, MÍNIMO 8 PÁRRAFOS LARGOS):
       - Usa párrafos: <p class="mb-5 text-justify text-slate-300 leading-relaxed">...</p>
       - Usa subtitulares para dividir temas: <h3 class="text-2xl font-extrabold text-white mt-8 mb-4 border-l-4 border-cyan-500 pl-3">...</h3>
       - Usa una cita destacada: <blockquote class="p-4 my-6 bg-slate-900/50 border-l-4 border-cyan-400 italic text-slate-300 rounded-r-lg">...</blockquote>
       - Usa listas si hay especificaciones: <ul class="list-disc pl-6 space-y-2 mb-6 text-slate-400 marker:text-cyan-500"><li>...</li></ul>
       - Resalta palabras clave con <strong>texto</strong>.
    4. PALABRAS CLAVE: Un solo término conceptual en inglés, SIN COMAS (ej: 'nvidia concept art').
    
    RESPONDE EXCLUSIVAMENTE EN JSON PLANO:
    {{
      "titulo": "Título profesional",
      "resumen": "Resumen corto",
      "cuerpo": "Contenido HTML extenso",
      "categoria": "{categoria}",
      "termino_busqueda_imagen": "termino corto sin comas"
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(safety_settings=seguridad, response_mime_type="application/json")
        )
        articulo_ia = json.loads(response.text)
    except Exception as e:
        print(f"❌ ERROR GEMINI: {e}")
        sys.exit(1)

    print("🖼️ Fase 3: Consolidando imágenes...")
    opciones_imagenes = extraer_imagenes_de_enlaces(enlaces_manuales)
    
    termino_img = articulo_ia.get("termino_busqueda_imagen", tema).split(",")[0].strip()
    try:
        with DDGS() as ddgs:
            for img in list(ddgs.images(f"{termino_img} gaming", max_results=10)):
                url = img.get('image')
                if url and url.startswith("http") and not any(x in url.lower() for x in ["icon", "logo", "avatar"]):
                    if url not in opciones_imagenes: opciones_imagenes.append(url)
                if len(opciones_imagenes) >= 5: break
    except Exception:
        pass
    
    respaldos = ["https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200", "https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=1200"]
    for r in respaldos:
        if len(opciones_imagenes) >= 3: break
        if r not in opciones_imagenes: opciones_imagenes.append(r)

    borrador_data = {
        "titulo": articulo_ia.get("titulo", "Artículo"),
        "resumen": articulo_ia.get("resumen", ""),
        "cuerpo": articulo_ia.get("cuerpo", ""),
        "categoria": categoria,
        "imagenes_candidatas": opciones_imagenes[:3]
    }
    
    with open(archivo_borrador, "w", encoding="utf-8") as f:
        json.dump(borrador_data, f, ensure_ascii=False, indent=2)
        
    print(f"🎉 ¡BORRADOR CREADO! Título: {borrador_data['titulo']}")

# =====================================================================
# INYECTAR ESTA LÓGICA EN bot_articulos.py DENTRO DE "2_publicar_borrador"
# =====================================================================
elif accion == "2_publicar_borrador":
    if not os.path.exists(archivo_borrador):
        print("❌ No hay borrador.")
        sys.exit(1)
        
    with open(archivo_borrador, "r", encoding="utf-8") as f:
        borrador = json.load(f)
        
    idx_foto = int(imagen_ok) - 1 if int(imagen_ok) in [1,2,3] else 0
    slug = re.sub(r'[^a-z0-9]+', '-', borrador["titulo"].lower()).strip('-')
    from datetime import datetime
    
    nuevo = {
        "id": f"art-{slug}",
        "titulo": borrador["titulo"],
        "resumen": borrador["resumen"],
        "cuerpo": borrador["cuerpo"],
        "categoria": borrador["categoria"],
        "imagen": borrador["imagenes_candidatas"][idx_foto],
        "fecha": datetime.now().strftime("%d %b, %Y"),
        "enlace": enlaces_manuales.split(",")[0].strip() if enlaces_manuales else "https://kazokugaming.com"
    }
    
    lista = []
    if os.path.exists(archivo_oficial):
        with open(archivo_oficial, "r", encoding="utf-8") as f:
            lista = json.load(f)
            if isinstance(lista, dict): lista = lista.get("articulos", [])
            
    lista.insert(0, nuevo)
    with open(archivo_oficial, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

    # 🌎 [NUEVO] GENERACIÓN DEL ARCHIVO HTML ESTÁTICO REAL PARA SEO
    os.makedirs("articulos", exist_ok=True)
    html_filename = f"articulos/{slug}.html"
    
    # Calculamos el tiempo de lectura para el HTML estático
    palabras = len(re.sub('<[^<]+?>', '', nuevo["cuerpo"]).split())
    tiempo_lectura = max(1, round(palabras / 200))

    plantilla_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{nuevo["titulo"]} | KazokuGaming</title>
    <meta name="description" content="{nuevo["resumen"]}">
    <meta property="og:title" content="{nuevo["titulo"]} | KazokuGaming">
    <meta property="og:description" content="{nuevo["resumen"]}">
    <meta property="og:image" content="{nuevo["imagen"]}">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0b0f19; scroll-behavior: smooth; }}
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-thumb {{ background: #1e293b; border-radius: 10px; }}
    </style>
</head>
<body class="text-slate-200 min-h-screen flex flex-col justify-between">
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex-grow w-full">
        <div id="cuerpo-global" class="flex flex-col lg:flex-row gap-12 relative">
            <div class="lg:w-3/4 w-full" id="area-articulo">
                <div class="mb-8">
                    <span class="text-xs bg-cyan-900/30 text-cyan-400 px-3 py-1 rounded border border-cyan-800/50 uppercase font-bold tracking-widest">{nuevo["categoria"]}</span>
                    <span class="text-slate-500 text-xs ml-3 border-l border-slate-700 pl-3">⏳ {tiempo_lectura} min de lectura</span>
                    <h1 class="text-4xl sm:text-5xl font-extrabold text-white mt-4 mb-4 leading-tight">{nuevo["titulo"]}</h1>
                    <p class="text-lg text-slate-400">{nuevo["resumen"]}</p>
                </div>
                <div class="w-full aspect-video rounded-2xl overflow-hidden mb-10 shadow-2xl shadow-black">
                    <img src="{nuevo["imagen"]}" class="w-full h-full object-cover" alt="{nuevo["titulo"]}">
                </div>
                <div class="prose-custom text-lg text-slate-300">{nuevo["cuerpo"]}</div>
            </div>
        </div>
    </main>
    <script src="../header.js"></script>
</body>
</html>"""

    with open(html_filename, "w", encoding="utf-8") as hf:
        hf.write(plantilla_html)
    print(f"🌎 HTML Estático creado en: {html_filename}")
        
    os.remove(archivo_borrador)
    print(f"🚀 ¡PUBLICADO! {nuevo['titulo']}")
