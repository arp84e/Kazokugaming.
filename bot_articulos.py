import os
import sys
import json
import re
from google import genai
from google.genai import types
from datetime import datetime

print("=== 🤖 KAZOKUBOT V3.5: MOTOR EDITORIAL MULTI-IMAGEN ===")

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

if accion == "1_generar_borrador":
    prompt = f"Escribe un artículo periodístico completamente nuevo, con un estilo editorial propio y pro-gaming sobre: {tema}. Debe encajar en la categoría {categoria}. Devuelve estrictamente un objeto JSON con las siguientes llaves: titulo, resumen, cuerpo (usa código HTML limpio con etiquetas p, h2, h3, ul, li; sin markdown), imagenes_candidatas (una lista con 3 URLs de imágenes de Unsplash en alta definición de tamaño 1200x675 o similar que encajen perfectamente con el tema)."
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(safety_settings=seguridad, response_mime_type="application/json")
        )
        borrador_data = json.loads(response.text)
        borrador_data["categoria"] = categoria
        with open(archivo_borrador, "w", encoding="utf-8") as f:
            json.dump(borrador_data, f, ensure_ascii=False, indent=2)
            
        print(f"🎉 ¡BORRADOR CREADO! Título: {borrador_data['titulo']}")
        
        # 🌟 MEJORA: IMPRIMIR LAS IMÁGENES EN LA CONSOLA DE GITHUB PARA EL USUARIO
        print("\n" + "="*60)
        print("🖼️  ENLACES DE LAS IMÁGENES SUGERIDAS POR LA IA (CÓPIALAS PARA VERLAS):")
        print("="*60)
        for i, url in enumerate(borrador_data.get("imagenes_candidatas", []), 1):
            print(f" 🔹 OPCIÓN [{i}]: {url}")
        print("="*60)
        print("👉 Evalúa cuál te gusta y selecciónala al ejecutar la acción '2_publicar_borrador'.")
        print("👉 Si deseas usarlas todas en el artículo, selecciona la opción 'Todas'.\n")
        
    except Exception as e:
        print(f"❌ ERROR CON LA IA: {e}")
        sys.exit(1)

elif accion == "2_publicar_borrador":
    if not os.path.exists(archivo_borrador):
        print("❌ No hay ningún borrador listo para publicar. Ejecuta primero la acción 1.")
        sys.exit(1)
        
    with open(archivo_borrador, "r", encoding="utf-8") as f:
        borrador = json.load(f)
        
    candidatas = borrador.get("imagenes_candidatas", ["https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"])
    
    # 🌟 MEJORA: LÓGICA DE SELECCIÓN INDIVIDUAL O MULTI-IMAGEN
    imagenes_seleccionadas = []
    if imagen_ok == "Todas":
        imagenes_seleccionadas = candidatas
        imagen_principal = candidatas[0] if len(candidatas) > 0 else "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    else:
        idx_foto = int(imagen_ok) - 1 if imagen_ok in ["1", "2", "3"] else 0
        if idx_foto >= len(candidatas): idx_foto = 0
        imagen_principal = candidatas[idx_foto]
        imagenes_seleccionadas = [imagen_principal]

    slug = re.sub(r'[^a-z0-9]+', '-', borrador["titulo"].lower()).strip('-')
    
    nuevo = {
        "id": f"art-{slug}",
        "titulo": borrador["titulo"],
        "resumen": borrador["resumen"],
        "cuerpo": borrador["cuerpo"],
        "categoria": borrador["categoria"],
        "imagen": imagen_principal, # Se mantiene para compatibilidad con index.html
        "imagenes_art": imagenes_seleccionadas, # Guardamos el array completo en la base de datos
        "fecha": datetime.now().strftime("%d %b, %Y"),
        "enlace": enlaces_manuales.split(",")[0].strip() if enlaces_manuales else "https://kazokugaming.com"
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

    # --- GENERACIÓN HTML ESTÁTICO INDIVIDUAL ---
    os.makedirs("articulos", exist_ok=True)
    html_filename = f"articulos/{slug}.html"
    
    palabras = len(re.sub('<[^<]+?>', '', nuevo["cuerpo"]).split())
    tiempo_lectura = max(1, round(palabras / 200))
    fecha_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # 🌟 MEJORA: CONSTRUIR LA GALERÍA VISUAL SI SE ELIGIÓ MÁS DE UNA IMAGEN
    html_galeria = ""
    if len(imagenes_seleccionadas) > 1:
        html_galeria += '''
        <div class="mt-12 pt-8 border-t border-slate-800/80">
            <h3 class="text-xl font-bold text-white mb-6 uppercase tracking-wider text-xs border-l-4 border-cyan-500 pl-3">Galería Multimedia</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">'''
        
        # Mostramos las imágenes secundarias restantes
        for img_sec in imagenes_seleccionadas[1:]:
            html_galeria += f'''
                <div class="rounded-2xl overflow-hidden border border-slate-800/60 shadow-lg aspect-[16/10] bg-slate-950">
                    <img src="{img_sec}" class="w-full h-full object-cover hover:scale-102 transition duration-500" alt="Contenido adicional" loading="lazy">
                </div>'''
                
        html_galeria += '''
            </div>
        </div>'''

    # Evitamos errores de llaves cruzadas convirtiendo el JSON-LD de SEO en un string puro desde Python
    json_ld_data = {
      "@context": "https://schema.org",
      "@type": "NewsArticle",
      "headline": nuevo["titulo"],
      "image": imagenes_seleccionadas,
      "datePublished": fecha_iso,
      "dateModified": fecha_iso,
      "author": {
        "@type": "Organization",
        "name": "KazokuGaming",
        "url": "https://kazokugaming.com"
      },
      "publisher": {
        "@type": "Organization",
        "name": "KazokuGaming",
        "logo": {
          "@type": "ImageObject",
          "url": "https://kazokugaming.com/favicon.png"
        }
      },
      "description": nuevo["resumen"]
    }
    json_ld_str = json.dumps(json_ld_data, ensure_ascii=False)

    plantilla_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{nuevo["titulo"]} | KazokuGaming</title>
    <meta name="description" content="{nuevo["resumen"]}">
    <link rel="icon" type="image/png" href="../favicon.png">
    
    <script type="application/ld+json">
    {json_ld_str}
    </script>

    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0b0f19; }}
        .prose-custom p {{ margin-bottom: 1.5em; line-height: 1.8; }}
        .prose-custom h2 {{ font-size: 1.75rem; font-weight: bold; margin-top: 2em; margin-bottom: 1em; color: #fff; border-left: 4px solid #06b6d4; padding-left: 12px; }}
        .prose-custom ul {{ list-style-type: disc; margin-left: 1.5em; margin-bottom: 1.5em; }}
        .prose-custom li {{ margin-bottom: 0.5em; }}
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
        <div class="w-full aspect-video rounded-3xl overflow-hidden mb-10 shadow-2xl border border-slate-800/50">
            <img src="{nuevo["imagen"]}" class="w-full h-full object-cover" alt="{nuevo["titulo"]}">
        </div>
        <div class="prose-custom text-lg text-slate-300 bg-slate-900/20 p-8 sm:p-10 rounded-3xl border border-slate-800/40 shadow-inner">
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
    print(f"🚀 ¡PUBLICADO EXITOSAMENTE! HTML creado en: {html_filename}")
