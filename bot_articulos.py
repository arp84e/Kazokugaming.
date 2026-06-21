import os
import sys
import json
import re
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from duckduckgo_search import DDGS
from datetime import datetime

print("=== 🤖 KAZOKUBOT V4.5: MOTOR ULTRA-SEO CON SELECCIÓN PERSONALIZADA DE IMÁGENES ===")

# Captura de variables de entorno de GitHub
accion = os.environ.get("INPUT_ACCION", "1_generar_borrador")
tema = os.environ.get("INPUT_TEMA", "")
categoria = os.environ.get("INPUT_CATEGORIA", "Tecnología")
enlaces_manuales = os.environ.get("INPUT_ENLACES", "")
imagen_ok = os.environ.get("INPUT_IMAGEN_OK", "1")
palabras_clave_imagenes = os.environ.get("INPUT_PALABRAS_CLAVE_IMAGENES", "")
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
    if not tema:
        print("❌ ERROR: Debes especificar un tema para el artículo.")
        sys.exit(1)

    contexto_noticias_web = ""
    print(f"🔍 1. Investigando en la red información reciente sobre: '{tema}'...")
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(tema, max_results=6):
                contexto_noticias_web += f"Fuente: {r['title']}\nDatos: {r['body']}\n\n"
    except Exception as e:
        print(f"⚠️ Alerta: No se pudo complementar con búsqueda web automática: {e}")

    contexto_enlaces_manuales = ""
    if enlaces_manuales:
        print("🔗 2. Extrayendo datos directamente de los enlaces manuales suministrados...")
        for url in enlaces_manuales.split(","):
            url = url.strip()
            if not url: continue
            try:
                res_web = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=10)
                soup = BeautifulSoup(res_web.text, 'html.parser')
                for s in soup(["script", "style", "header", "footer", "nav"]):
                    s.decompose()
                texto_limpio = " ".join(soup.get_text().split())[:2500]
                contexto_enlaces_manuales += f"Contenido de Referencia ({url}):\n{texto_limpio}\n\n"
            except Exception as e:
                print(f"⚠️ No se pudo raspar la URL {url}: {e}")

    print("🧠 3. Solicitando a Gemini redacción profesional analítica e inédita...")
    prompt = f"""
    Eres el redactor jefe técnico y especialista en periodismo de videojuegos de KazokuGaming. Tu misión es escribir un artículo de prensa de nivel excepcional, profundamente analítico, profesional y 100% original sobre el tema: '{tema}'.
    
    Para asegurar la máxima veracidad, actualidad y frescura, debes fusionar de manera analítica la información de las siguientes fuentes de la red:
    
    [INFORMACIÓN RECIENTE DE INTERNET]
    {contexto_noticias_web}
    
    [DATOS EXTRAÍDOS DE ENLACES ESPECÍFICOS]
    {contexto_enlaces_manuales}
    
    Reglas estrictas de redacción para evitar plagios y mejorar SEO:
    1. No copies frases textuales de las fuentes; reescribe, sintetiza y aporta un enfoque crítico/editorial propio del ecosistema gaming.
    2. Estructura el artículo de forma elegante y madura.
    3. Devuelve estrictamente un objeto JSON con las llaves: 'titulo', 'resumen' y 'cuerpo'.
    4. El 'cuerpo' debe contener exclusivamente código HTML limpio utilizando párrafos (<p>), subtítulos (<h2>, <h3>), listas (<ul>, <li>) y énfasis (<strong>). No uses markdown, ni bloques de código formateados (```html).
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(safety_settings=seguridad, response_mime_type="application/json")
        )
        borrador_data = json.loads(response.text)
        borrador_data["categoria"] = categoria
        
        # 🖼️ BÚSQUEDA DE IMÁGENES LIBRES DE COPYRIGHT (HASTA 10)
        termino_img = palabras_clave_imagenes if palabras_clave_imagenes.strip() else tema
        print(f"🖼️ 4. Buscando en la red imágenes libres de derechos para: '{termino_img}'...")
        
        imagenes_encontradas = []
        try:
            with DDGS() as ddgs:
                res_images = [r for r in ddgs.images(termino_img, max_results=30, license='Public')]
                for r in res_images:
                    img_url = r.get('image')
                    if img_url and (img_url.startswith('http://') or img_url.startswith('https://')):
                        imagenes_encontradas.append(img_url)
                    if len(imagenes_encontradas) >= 10:
                        break
        except Exception as img_err:
            print(f"⚠️ Error al buscar imágenes en DuckDuckGo: {img_err}")

        if len(imagenes_encontradas) < 10:
            respaldos = [
                "[https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200](https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200)",
                "[https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=1200](https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=1200)",
                "[https://images.unsplash.com/photo-1538481199705-c710c4e965fc?q=80&w=1200](https://images.unsplash.com/photo-1538481199705-c710c4e965fc?q=80&w=1200)",
                "[https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1200](https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1200)",
                "[https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?q=80&w=1200](https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?q=80&w=1200)",
                "[https://images.unsplash.com/photo-1552820728-8b83bb6b773f?q=80&w=1200](https://images.unsplash.com/photo-1552820728-8b83bb6b773f?q=80&w=1200)",
                "[https://images.unsplash.com/photo-1512512578047-dfb367046420?q=80&w=1200](https://images.unsplash.com/photo-1512512578047-dfb367046420?q=80&w=1200)",
                "[https://images.unsplash.com/photo-1593305841991-05c297ba4575?q=80&w=1200](https://images.unsplash.com/photo-1593305841991-05c297ba4575?q=80&w=1200)",
                "[https://images.unsplash.com/photo-1560253023-3ec5d502959f?q=80&w=1200](https://images.unsplash.com/photo-1560253023-3ec5d502959f?q=80&w=1200)",
                "[https://images.unsplash.com/photo-1612287230202-1bf1d85d1bdf?q=80&w=1200](https://images.unsplash.com/photo-1612287230202-1bf1d85d1bdf?q=80&w=1200)"
            ]
            while len(imagenes_encontradas) < 10:
                imagenes_encontradas.append(respaldos[len(imagenes_encontradas) % len(respaldos)])

        borrador_data["imagenes_candidatas"] = imagenes_encontradas[:10]
        
        with open(archivo_borrador, "w", encoding="utf-8") as f:
            json.dump(borrador_data, f, ensure_ascii=False, indent=2)
            
        print(f"🎉 ¡BORRADOR EDITORIAL PREPARADO! Título: {borrador_data['titulo']}")
        print("\n" + "="*80)
        print("🖼️  CATÁLOGO DE 10 IMÁGENES COMPILADAS (LIBRES DE DERECHOS):")
        print("="*80)
        for idx, url in enumerate(borrador_data["imagenes_candidatas"], 1):
            print(f" 🔹 OPCIÓN [{idx}]: {url}")
        print("="*80)
        print("👉 Evalúa los recursos y selecciona los índices correspondientes para publicar.")
        print("👉 Ejemplo de selección múltiple personalizada: 1,3,4,7,9")
        print("👉 Para inyectar las 10 imágenes en una galería responsiva escribe: Todas\n")
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN PROCESO DE BORRADOR: {e}")
        sys.exit(1)

elif accion == "2_publicar_borrador":
    if not os.path.exists(archivo_borrador):
        print("❌ ERROR: No hay ningún borrador listo para compilar. Ejecuta la Acción 1 primero.")
        sys.exit(1)
        
    with open(archivo_borrador, "r", encoding="utf-8") as f:
        borrador = json.load(f)
        
    candidatas = borrador.get("imagenes_candidatas", [])
    
    # 🌟 LÓGICA DE SELECCIÓN MULTIPLE PERSONALIZADA (EJ: 1,3,4,7)
    imagenes_seleccionadas = []
    imagen_ok_limpio = str(imagen_ok).strip()
    
    if imagen_ok_limpio.lower() == "todas":
        imagenes_seleccionadas = candidatas
    else:
        # Extraemos los números de la cadena ingresada por el usuario
        indices_usuario = [int(x.strip()) - 1 for x in imagen_ok_limpio.split(",") if x.strip().isdigit()]
        for idx in indices_usuario:
            if 0 <= idx < len(candidatas):
                imagenes_seleccionadas.append(candidatas[idx])
                
    # Si la lista quedó vacía por un error de formato, asignamos la primera por defecto
    if not imagenes_seleccionadas:
        imagenes_seleccionadas = [candidatas[0]] if candidatas else ["[https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200](https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200)"]
        
    imagen_principal = imagenes_seleccionadas[0]

    slug = re.sub(r'[^a-z0-9]+', '-', borrador["titulo"].lower()).strip('-')
    
    nuevo = {
        "id": f"art-{slug}",
        "titulo": borrador["titulo"],
        "resumen": borrador["resumen"],
        "cuerpo": borrador["cuerpo"],
        "categoria": borrador["categoria"],
        "imagen": imagen_principal,
        "imagenes_art": imagenes_seleccionadas,
        "fecha": datetime.now().strftime("%d %b, %Y"),
        "enlace": enlaces_manuales.split(",")[0].strip() if enlaces_manuales else "[https://kazokugaming.com](https://kazokugaming.com)"
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

    # GENERACIÓN DEL TEMPLATE HTML ESTÁTICO (SEO)
    os.makedirs("articulos", exist_ok=True)
    html_filename = f"articulos/{slug}.html"
    
    palabras = len(re.sub('<[^<]+?>', '', nuevo["cuerpo"]).split())
    tiempo_lectura = max(1, round(palabras / 200))
    fecha_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # DISEÑO DE LA GALERÍA EXTENDIDA CON LAS IMÁGENES SELECCIONADAS
    html_galeria = ""
    if len(imagenes_seleccionadas) > 1:
        html_galeria += '''
        <div class="mt-12 pt-8 border-t border-slate-800/60">
            <h3 class="text-xs font-black text-cyan-400 uppercase tracking-widest mb-6 border-l-4 border-cyan-500 pl-3">Soporte Multimedia Ampliado</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">'''
        
        for img_sec in imagenes_seleccionadas[1:]:
            html_galeria += f'''
                <div class="rounded-2xl overflow-hidden border border-slate-800/50 shadow-md aspect-[16/10] bg-slate-950 group">
                    <img src="{img_sec}" class="w-full h-full object-cover group-hover:scale-103 transition duration-500" alt="Recurso multimedia libre" loading="lazy" onerror="this.src='[https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=600](https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=600)'">
                </div>'''
                
        html_galeria += '''
            </div>
        </div>'''

    json_ld_data = {
      "@context": "[https://schema.org](https://schema.org)",
      "@type": "NewsArticle",
      "headline": nuevo["titulo"],
      "image": imagenes_seleccionadas,
      "datePublished": fecha_iso,
      "dateModified": fecha_iso,
      "author": {
        "@type": "Organization",
        "name": "KazokuGaming",
        "url": "[https://kazokugaming.com](https://kazokugaming.com)"
      },
      "publisher": {
        "@type": "Organization",
        "name": "KazokuGaming",
        "logo": {
          "@type": "ImageObject",
          "url": "[https://kazokugaming.com/favicon.png](https://kazokugaming.com/favicon.png)"
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

    <link href="[https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700;800&display=swap](https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700;800&display=swap)" rel="stylesheet">
    <script src="[https://cdn.tailwindcss.com](https://cdn.tailwindcss.com)"></script>
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
            <img src="{nuevo["imagen"]}" class="w-full h-full object-cover" alt="{nuevo["titulo"]}" onerror="this.src='[https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200](https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200)'">
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
    print(f"🚀 ¡PUBLICACIÓN GLOBAL EMITIDA! HTML estructurado en: {html_filename}")
