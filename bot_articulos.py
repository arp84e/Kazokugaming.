import os
import sys
import json
import re
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from datetime import datetime
import warnings

# Silenciar las advertencias inofensivas de librerías de terceros
warnings.filterwarnings("ignore")

# Importación segura del buscador DuckDuckGo
try:
    from duckduckgo_search import DDGS
except ImportError:
    try:
        from ddgs import DDGS
    except ImportError:
        sys.exit("❌ ERROR CRÍTICO: No se pudo cargar el motor de búsqueda. Verifica la instalación.")

print("=== 🤖 KAZOKUBOT V7.0: MOTOR DE MÁXIMA PRECISIÓN Y RASTREO AMPLIADO ===")

# Captura de variables de entorno de GitHub
accion = os.environ.get("INPUT_ACCION", "1_generar_borrador")
tema = os.environ.get("INPUT_TEMA", "")
categoria = os.environ.get("INPUT_CATEGORIA", "Tecnología")
enlaces_manuales = os.environ.get("INPUT_ENLACES", "")
imagen_ok = os.environ.get("INPUT_IMAGEN_OK", "1")
palabras_clave_imagenes = os.environ.get("INPUT_PALABRAS_CLAVE_IMAGENES", "")
id_objetivo = os.environ.get("INPUT_ID_OBJETIVO", "")
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    sys.exit("❌ ERROR: No se configuró GEMINI_API_KEY.")

client = genai.Client(api_key=api_key)
archivo_borrador = "articulos_borrador.json"
archivo_oficial = "articulos.json"

seguridad = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

# 🛠️ SISTEMA DE AUTO-REINTENTO PARA SERVIDORES SATURADOS O LÍMITES DE CUOTA
def generar_texto_ia_con_reintentos(prompt_text, retries=3):
    for intento in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash", 
                contents=prompt_text,
                config=types.GenerateContentConfig(safety_settings=seguridad, response_mime_type="application/json")
            )
            return response
        except Exception as e:
            error_str = str(e).upper()
            if "503" in error_str or "UNAVAILABLE" in error_str or "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"⚠️ Servidores de Google al límite de capacidad (Intento {intento+1}/{retries}). Esperando 15 segundos...")
                time.sleep(15)
                if intento == retries - 1:
                    raise Exception("❌ Los servidores de la API siguen saturados. Por favor, intenta de nuevo en un par de minutos.")
            else:
                raise e

# 🛠️ FUNCIÓN PARA LIMPIAR JSON SUCIO DE LA IA
def extraer_json_seguro(texto_ia):
    match = re.search(r'\{.*\}', texto_ia.strip(), re.DOTALL)
    if match:
        return json.loads(match.group(0))
    else:
        return json.loads(texto_ia.replace("```json", "").replace("```", "").strip())

# 🛠️ FUNCIÓN MAESTRA: CONSTRUCTOR DE HTML CON IMÁGENES INTERCALADAS
def construir_y_guardar_html(articulo_dict):
    slug = articulo_dict["id"].replace("art-", "")
    os.makedirs("articulos", exist_ok=True)
    html_filename = f"articulos/{slug}.html"
    
    imagenes_seleccionadas = articulo_dict.get("imagenes_art", [articulo_dict.get("imagen")])
    termino_img_fallback = articulo_dict.get("palabra_clave_usada", "epic gaming")
    termino_url_fallback = urllib.parse.quote(termino_img_fallback)
    
    cuerpo_html = articulo_dict["cuerpo"]
    soup = BeautifulSoup(cuerpo_html, 'html.parser')
    bloques_texto = [b for b in soup.find_all(['p', 'h2', 'h3']) if len(b.get_text(strip=True)) > 30]
    
    html_galeria = ""
    if len(imagenes_seleccionadas) > 1:
        imagenes_extra = imagenes_seleccionadas[1:]
        num_bloques = len(bloques_texto)
        
        if num_bloques > 0:
            imgs_a_insertar = imagenes_extra[:num_bloques]
            imgs_sobrantes = imagenes_extra[num_bloques:]
            step = max(1, num_bloques // (len(imgs_a_insertar) + 1))
            
            for i, img_url in enumerate(imgs_a_insertar):
                target_idx = (i + 1) * step
                if target_idx >= num_bloques: target_idx = num_bloques - 1
                
                fallback = f"https://image.pollinations.ai/prompt/{termino_url_fallback}%20extra%20{i}?width=1200&height=675&nologo=true"
                img_tag = soup.new_tag('img', src=img_url)
                img_tag['class'] = "w-full aspect-[16/9] rounded-3xl overflow-hidden my-10 shadow-2xl border border-slate-700/50 object-cover"
                img_tag['loading'] = "lazy"
                img_tag['referrerpolicy'] = "no-referrer"
                img_tag['onerror'] = f"this.src='{fallback}'"
                
                bloques_texto[target_idx].insert_after(img_tag)
                
            articulo_dict["cuerpo"] = str(soup)
            
            if imgs_sobrantes:
                html_galeria += '''<div class="mt-12 pt-8 border-t border-slate-800/60"><h3 class="text-xs font-black text-cyan-400 uppercase tracking-widest mb-6 border-l-4 border-cyan-500 pl-3">Galería Multimedia</h3><div class="grid grid-cols-1 sm:grid-cols-2 gap-6">'''
                for i, img_sec in enumerate(imgs_sobrantes):
                    fallback = f"https://image.pollinations.ai/prompt/{termino_url_fallback}%20gallery%20{i}?width=1200&height=675&nologo=true"
                    html_galeria += f'''<div class="rounded-2xl overflow-hidden border border-slate-800/50 shadow-md aspect-[16/9] bg-slate-950 group"><img src="{img_sec}" referrerpolicy="no-referrer" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" loading="lazy" onerror="this.src='{fallback}'"></div>'''
                html_galeria += '''</div></div>'''

    palabras = len(re.sub('<[^<]+?>', '', articulo_dict["cuerpo"]).split())
    tiempo_lectura = max(1, round(palabras / 200))
    fecha_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00")

    json_ld_data = {
      "@context": "https://schema.org",
      "@type": "NewsArticle",
      "headline": articulo_dict["titulo"],
      "image": imagenes_seleccionadas,
      "datePublished": fecha_iso,
      "dateModified": fecha_iso,
      "author": {"@type": "Organization", "name": "KazokuGaming"},
      "publisher": {"@type": "Organization", "name": "KazokuGaming", "logo": {"@type": "ImageObject", "url": "https://kazokugaming.com/favicon.png"}},
      "description": articulo_dict["resumen"]
    }
    json_ld_str = json.dumps(json_ld_data, ensure_ascii=False)

    plantilla_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{articulo_dict["titulo"]} | KazokuGaming</title>
    <link rel="icon" type="image/png" href="../favicon.png">
    <script type="application/ld+json">{json_ld_str}</script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0b0f19; }}
        .prose-custom * {{ color: #cbd5e1 !important; background-color: transparent !important; font-family: inherit !important; line-height: 1.8 !important; }}
        .prose-custom h2, .prose-custom h3 {{ color: #f8fafc !important; font-weight: 800 !important; margin-top: 2.5em !important; margin-bottom: 1em !important; border-left: 4px solid #06b6d4; padding-left: 12px; }}
        .prose-custom strong, .prose-custom b {{ color: #22d3ee !important; font-weight: 700 !important; }}
        .prose-custom p {{ margin-bottom: 1.5em !important; font-size: 1.125rem !important; }}
        .prose-custom ul {{ list-style-type: disc !important; margin-left: 1.5em !important; margin-bottom: 1.5em !important; }}
    </style>
</head>
<body class="text-slate-200 min-h-screen flex flex-col justify-between">
    <div id="header-container"></div>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex-grow w-full">
        <div class="mb-8">
            <span class="text-xs bg-cyan-900/30 text-cyan-400 px-3 py-1 rounded border border-cyan-800/50 uppercase font-bold tracking-widest">{articulo_dict["categoria"]}</span>
            <span class="text-slate-500 text-xs ml-3 border-l border-slate-700 pl-3">⏳ {tiempo_lectura} min de lectura</span>
            <h1 class="text-4xl sm:text-5xl font-extrabold text-white mt-4 mb-4 leading-tight">{articulo_dict["titulo"]}</h1>
            <p class="text-lg text-slate-400">{articulo_dict["resumen"]}</p>
        </div>
        <div class="w-full aspect-[16/9] rounded-3xl overflow-hidden mb-10 shadow-2xl border border-slate-800/50 bg-slate-900">
            <img src="{articulo_dict["imagen"]}" referrerpolicy="no-referrer" class="w-full h-full object-cover" onerror="this.src='https://image.pollinations.ai/prompt/{termino_url_fallback}%20cover?width=1200&height=675&nologo=true'">
        </div>
        <div class="prose-custom bg-slate-900/40 p-8 sm:p-10 rounded-3xl border border-slate-700/50 shadow-lg">
            {articulo_dict["cuerpo"]}
        </div>
        {html_galeria}
    </main>
    <script src="../header.js"></script>
</body>
</html>'''

    with open(html_filename, "w", encoding="utf-8") as hf:
        hf.write(plantilla_html)
    print(f"🚀 ¡MAQUETACIÓN ESTÁTICA EXITOSA! Creado en: {html_filename}")

# ==========================================================
# ACCIÓN 1: GENERAR BORRADOR
# ==========================================================
if accion == "1_generar_borrador":
    if not tema: sys.exit("❌ ERROR: Especifica un tema.")
    
    contexto = ""
    try:
        with DDGS() as ddgs:
            print(f"🔍 Rastreando noticias recientes y artículos web sobre: '{tema}'...")
            # 🌟 MEJORA: Rastreo doble para mayor precisión periodística
            try:
                for r in ddgs.news(tema, max_results=5):
                    contexto += f"NOTICIA: {r.get('title', '')}\nDatos: {r.get('body', '')}\n\n"
            except: pass
            
            try:
                for r in ddgs.text(tema, max_results=5):
                    contexto += f"WEB: {r.get('title', '')}\nDatos: {r.get('body', '')}\n\n"
            except: pass
    except Exception as e:
        print(f"⚠️ Aviso en DuckDuckGo Web: {e}")

    if enlaces_manuales:
        print("🔗 Procesando enlaces manuales...")
        for url in enlaces_manuales.split(","):
            if not url.strip(): continue
            try:
                res_web = requests.get(url.strip(), headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                soup = BeautifulSoup(res_web.text, 'html.parser')
                for s in soup(["script", "style", "nav", "footer", "aside"]): s.decompose()
                contexto += " ".join(soup.get_text().split())[:2500] + "\n\n"
            except Exception as e:
                print(f"⚠️ Aviso extrayendo URL: {e}")

    prompt = f"""Eres el redactor jefe de KazokuGaming. Escribe un artículo de prensa excepcional, profundo y 100% original sobre: '{tema}'.
    Usa esta info fresca: {contexto}
    REGLA VITAL: Devuelve HTML puro con <p>, <h2>, <ul>, <li> y <strong>. SIN ESTILOS CSS EN LÍNEA.
    Devuelve un JSON estricto con: 'titulo', 'resumen' y 'cuerpo'."""

    try:
        print("🧠 Procesando datos con Gemini AI...")
        response = generar_texto_ia_con_reintentos(prompt)
        
        borrador_data = extraer_json_seguro(response.text)
        borrador_data["categoria"] = categoria
        
        # 🌟 MEJORA MÁXIMA EN BÚSQUEDA DE IMÁGENES
        termino_base = palabras_clave_imagenes if palabras_clave_imagenes.strip() else tema
        print(f"🖼️ Buscando imágenes de ALTA CALIDAD para: '{termino_base}'...")
        
        imagenes = []
        try:
            with DDGS() as ddgs:
                # Quitamos restricción de licencia para usar el Fair Use de prensa y filtramos por tamaño Grande (HD/4K)
                for r in ddgs.images(termino_base, max_results=40, size="Large"):
                    img_url = r.get('image', '')
                    # Filtro de calidad: Evitamos SVG, iconos y logos que arruinan la maquetación
                    if img_url.startswith('http') and not any(x in img_url.lower() for x in ['.svg', 'logo', 'icon', 'avatar']): 
                        imagenes.append(img_url)
                    if len(imagenes) >= 10: break
        except Exception as e:
            print(f"⚠️ Aviso buscador de imágenes: {e}")

        # 🌟 NUEVO FALLBACK INTELIGENTE: 
        # Si no encuentra 10 reales, la IA generará imágenes estrictamente de TU TEMA en lugar de teclados genéricos.
        borrador_data["palabra_clave_usada"] = termino_base
        termino_url = urllib.parse.quote(termino_base)
        while len(imagenes) < 10:
            imagenes.append(f"https://image.pollinations.ai/prompt/{termino_url}%20epic%20high%20quality%20{len(imagenes)}?width=1200&height=675&nologo=true")

        borrador_data["imagenes_candidatas"] = imagenes[:10]
        
        with open(archivo_borrador, "w", encoding="utf-8") as f:
            json.dump(borrador_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n🎉 ¡BORRADOR PREPARADO! Título: {borrador_data['titulo']}")
        print("\n" + "="*80)
        print(f"🖼️ CATÁLOGO DE 10 IMÁGENES DE ALTA PRECISIÓN PARA '{termino_base}':")
        print("="*80)
        for idx, url in enumerate(borrador_data["imagenes_candidatas"], 1):
            print(f" 🔹 OPCIÓN [{idx}]: {url}")
        print("="*80)
        print("👉 Haz clic en los enlaces para revisarlas. Luego ejecuta la Acción 2 y escribe los números deseados (ej: 1,3,4) o 'Todas'.\n")
        
    except Exception as e:
        sys.exit(f"❌ ERROR CRÍTICO: {e}")

# ==========================================================
# ACCIÓN 2: PUBLICAR BORRADOR
# ==========================================================
elif accion == "2_publicar_borrador":
    if not os.path.exists(archivo_borrador): sys.exit("❌ ERROR: No hay borrador.")
    with open(archivo_borrador, "r", encoding="utf-8") as f: borrador = json.load(f)
        
    candidatas = borrador.get("imagenes_candidatas", [])
    imagenes_seleccionadas = []
    
    if str(imagen_ok).strip().lower() == "todas":
        imagenes_seleccionadas = candidatas
    else:
        indices = [int(x.strip()) - 1 for x in str(imagen_ok).split(",") if x.strip().isdigit()]
        imagenes_seleccionadas = [candidatas[i] for i in indices if 0 <= i < len(candidatas)]
                
    if not imagenes_seleccionadas: 
        termino_url_fallback = urllib.parse.quote(borrador.get("palabra_clave_usada", "gaming"))
        imagenes_seleccionadas = [candidatas[0]] if candidatas else [f"https://image.pollinations.ai/prompt/{termino_url_fallback}?width=1200&height=675&nologo=true"]
        
    slug = re.sub(r'[^a-z0-9]+', '-', borrador["titulo"].lower()).strip('-')
    nuevo = {
        "id": f"art-{slug}",
        "titulo": borrador["titulo"],
        "resumen": borrador["resumen"],
        "cuerpo": borrador["cuerpo"],
        "categoria": borrador["categoria"],
        "imagen": imagenes_seleccionadas[0],
        "imagenes_art": imagenes_seleccionadas,
        "palabra_clave_usada": borrador.get("palabra_clave_usada", "gaming"),
        "fecha": datetime.now().strftime("%d %b, %Y")
    }
    
    lista = []
    if os.path.exists(archivo_oficial):
        with open(archivo_oficial, "r", encoding="utf-8") as f:
            try: lista = json.load(f).get("articulos", []) if isinstance(json.load(f), dict) else json.load(f)
            except: pass
            
    lista.insert(0, nuevo)
    with open(archivo_oficial, "w", encoding="utf-8") as f: json.dump(lista, f, ensure_ascii=False, indent=2)

    construir_y_guardar_html(nuevo)

# ==========================================================
# ACCIÓN 3: ELIMINAR ARTÍCULO
# ==========================================================
elif accion == "3_eliminar_articulo":
    if not id_objetivo: sys.exit("❌ ERROR: Especifica ID o título.")
    if os.path.exists(archivo_oficial):
        with open(archivo_oficial, "r", encoding="utf-8") as f:
            lista = json.load(f)
        nueva_lista = [a for a in lista if id_objetivo.lower() not in a["id"].lower() and id_objetivo.lower() not in a["titulo"].lower()]
        if len(nueva_lista) < len(lista):
            with open(archivo_oficial, "w", encoding="utf-8") as f: json.dump(nueva_lista, f, ensure_ascii=False, indent=2)
            print("✅ Artículo(s) eliminado(s) de la base de datos.")
        else:
            sys.exit("⚠️ No se encontró el artículo.")

# ==========================================================
# ACCIÓN 4: MODIFICAR / MEJORAR ARTÍCULO EXISTENTE
# ==========================================================
elif accion == "4_modificar_articulo":
    if not id_objetivo: sys.exit("❌ ERROR: Especifica el ID o título del artículo a modificar.")
    if not tema: sys.exit("❌ ERROR: En la casilla 'Tema', escribe qué deseas mejorar (Ej: Añade un párrafo sobre optimización).")
    
    if os.path.exists(archivo_oficial):
        with open(archivo_oficial, "r", encoding="utf-8") as f:
            lista = json.load(f)
            
        articulo_encontrado = None
        for i, art in enumerate(lista):
            if id_objetivo.lower() in art["id"].lower() or id_objetivo.lower() in art["titulo"].lower():
                articulo_encontrado = art
                indice = i
                break
                
        if not articulo_encontrado:
            sys.exit("⚠️ No se encontró el artículo a modificar.")
            
        print(f"✏️ Modificando artículo: {articulo_encontrado['titulo']}")
        print("🧠 Enviando instrucciones de mejora a la IA...")
        
        prompt = f"""Eres el redactor jefe. Toma este artículo existente y aplica las siguientes modificaciones/mejoras: '{tema}'.
        TÍTULO ACTUAL: {articulo_encontrado['titulo']}
        RESUMEN ACTUAL: {articulo_encontrado['resumen']}
        CUERPO ACTUAL: {articulo_encontrado['cuerpo']}
        
        REGLA VITAL: Mantén el formato en HTML limpio (<p>, <h2>, <ul>). NO uses estilos en línea.
        Devuelve un JSON con: 'titulo', 'resumen' y 'cuerpo' actualizado."""

        try:
            response = generar_texto_ia_con_reintentos(prompt)
            data_modificada = extraer_json_seguro(response.text)
            
            lista[indice]["titulo"] = data_modificada["titulo"]
            lista[indice]["resumen"] = data_modificada["resumen"]
            lista[indice]["cuerpo"] = data_modificada["cuerpo"]
            
            with open(archivo_oficial, "w", encoding="utf-8") as f: 
                json.dump(lista, f, ensure_ascii=False, indent=2)
                
            construir_y_guardar_html(lista[indice])
            print(f"✅ ¡Artículo modificado, sobreescrito y actualizado con éxito!")
            
        except Exception as e:
            sys.exit(f"❌ ERROR AL MODIFICAR: {e}")
