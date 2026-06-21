import os
import sys
import json
import re
import requests
from google import genai
from google.genai import types

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

if accion == "1_generar_borrador":
    prompt = f"Escribe un artículo detallado sobre {tema} para la categoría {categoria}. Devuelve un JSON estricto con: titulo, resumen, cuerpo (en HTML, sin markdown, usando etiquetas p, h2, h3, ul, li), imagenes_candidatas (lista de 3 urls de unsplash)."
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        borrador_data = json.loads(response.text)
        borrador_data["categoria"] = categoria
        with open(archivo_borrador, "w", encoding="utf-8") as f:
            json.dump(borrador_data, f, ensure_ascii=False, indent=2)
        print(f"🎉 ¡BORRADOR CREADO! Título: {borrador_data['titulo']}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

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
        "imagen": borrador.get("imagenes_candidatas", ["https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"])[idx_foto],
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

    # --- PASO 1: GENERACIÓN HTML ESTÁTICO PARA SEO ---
    os.makedirs("articulos", exist_ok=True)
    html_filename = f"articulos/{slug}.html"
    
    palabras = len(re.sub('<[^<]+?>', '', nuevo["cuerpo"]).split())
    tiempo_lectura = max(1, round(palabras / 200))

    plantilla_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{nuevo["titulo"]} | KazokuGaming</title>
    <meta name="description" content="{nuevo["resumen"]}">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0b0f19; }}
        .prose-custom p {{ margin-bottom: 1.5em; line-height: 1.8; }}
        .prose-custom h2 {{ font-size: 1.75rem; font-weight: bold; margin-top: 2em; margin-bottom: 1em; color: #fff; }}
        .prose-custom ul {{ list-style-type: disc; margin-left: 1.5em; margin-bottom: 1.5em; }}
    </style>
</head>
<body class="text-slate-200 min-h-screen flex flex-col justify-between">
    <div id="header-container"></div>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex-grow w-full">
        <div class="mb-8">
            <span class="text-xs bg-cyan-900/30 text-cyan-400 px-3 py-1 rounded border border-cyan-800/50 uppercase font-bold">{nuevo["categoria"]}</span>
            <span class="text-slate-500 text-xs ml-3 border-l border-slate-700 pl-3">⏳ {tiempo_lectura} min de lectura</span>
            <h1 class="text-4xl sm:text-5xl font-extrabold text-white mt-4 mb-4">{nuevo["titulo"]}</h1>
            <p class="text-lg text-slate-400">{nuevo["resumen"]}</p>
        </div>
        <img src="{nuevo["imagen"]}" class="w-full aspect-video rounded-2xl object-cover mb-10 shadow-2xl border border-slate-800" alt="{nuevo["titulo"]}">
        <div class="prose-custom text-lg text-slate-300 bg-slate-900/30 p-8 rounded-2xl border border-slate-800/50">
            {nuevo["cuerpo"]}
        </div>
    </main>
    <script src="../header.js"></script>
</body>
</html>'''

    with open(html_filename, "w", encoding="utf-8") as hf:
        hf.write(plantilla_html)
        
    os.remove(archivo_borrador)
    print(f"🚀 ¡PUBLICADO! HTML Estático creado en: {html_filename}")
