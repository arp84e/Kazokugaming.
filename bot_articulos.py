import os
import sys
import json
import re
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from duckduckgo_search import DDGS

print("=== 🤖 KAZOKUBOT V2.1: MOTOR EDITORIAL PERFECCIONADO ===")

# 📥 1. CAPTURA DE ENTRADAS DESDE GITHUB ACTIONS
accion = os.environ.get("INPUT_ACCION", "1_generar_borrador")
tema = os.environ.get("INPUT_TEMA", "")
categoria = os.environ.get("INPUT_CATEGORIA", "Tecnología")
enlaces_manuales = os.environ.get("INPUT_ENLACES", "")
imagen_ok = os.environ.get("INPUT_IMAGEN_OK", "1")
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: No se configuró GEMINI_API_KEY en los secretos del repositorio.")
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

# 🧲 FUNCIÓN MAESTRA: Extraer imágenes reales de los enlaces proporcionados
def extraer_imagenes_de_enlaces(texto_enlaces):
    imagenes_encontradas = []
    if not texto_enlaces:
        return imagenes_encontradas
        
    urls = [u.strip() for u in texto_enlaces.split(",") if u.strip().startswith("http")]
    print(f"🔗 Analizando {len(urls)} enlace(s) manual(es) para extraer imágenes originales...")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # SINTAXIS CORREGIDA: Buscamos las propiedades OpenGraph sin romper los argumentos de BS4
                og_meta = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
                if og_meta and og_meta.get("content"):
                    img_url = og_meta["content"].strip()
                    if img_url.startswith("http") and img_url not in imagenes_encontradas:
                        print(f"   📸 Portada SEO detectada: {img_url[:60]}...")
                        imagenes_encontradas.append(img_url)
                
                for img_tag in soup.find_all("img"):
                    src = img_tag.get("src") or img_tag.get("data-src") or img_tag.get("lazy-src")
                    if src and src.startswith("http"):
                        if not any(x in src.lower() for x in ["icon", "logo", "avatar", "sprite", "nav", "header", "badge"]):
                            if src not in imagenes_encontradas:
                                imagenes_encontradas.append(src)
                    if len(imagenes_encontradas) >= 4:
                        break
        except Exception as e:
            print(f"   ⚠️ No se pudo escanear el enlace {url}: {e}")
            
    return imagenes_encontradas

# =====================================================================
# 🔄 FASE 1: GENERAR UN NUEVO BORRADOR
# =====================================================================
if accion == "1_generar_borrador":
    if not tema:
        print("❌ ERROR: Para generar un borrador necesitas escribir un 'Tema o Título'.")
        sys.exit(1)
        
    print(f"🔎 Fase 1: Investigando contexto para el tema: '{tema}'...")
    contexto_busqueda = ""
    
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(f"{tema} gaming technology news", max_results=4))
            for res in resultados:
                contexto_busqueda += f"- {res['title']}: {res['body']} (Fuente: {res['href']})\n"
    except Exception as e:
        print(f"⚠️ Nota: Buscador de contexto omitido ({e}). Usaremos tus fuentes directas.")

    if enlaces_manuales:
        contexto_busqueda += f"\n[FUENTES OFICIALES PRIORITARIAS]:\n{enlaces_manuales}\n"

    print("✍️ Fase 2: Redactando contenido y optimizando palabras clave multimedia con Gemini...")
    
    prompt = f"""
    Actúa como un Redactor Jefe Senior y experto en SEO para la revista digital KazokuGaming.
    Crea un artículo técnico, original, llamativo y muy profesional basado en estos datos:
    
    TEMA DE ENTRADA: {tema}
    CATEGORÍA: {categoria}
    INVESTIGACIÓN DE SOPORTE:
    {contexto_busqueda}
    
    INSTRUCCIONES DE FORMATO:
    1. TÍTULO: Sumamente profesional, magnético y optimizado para SEO. Max 70 caracteres.
    2. RESUMEN CORTO: Un gancho de 2 líneas para la tarjeta de la página de inicio.
    3. CUERPO: Formato HTML limpio. Usa párrafos con (<p class="mb-4 text-justify">...</p>), sub-titulares interesantes con h3 (<h3 class="text-xl font-bold text-white mt-6 mb-3">...</h3>) y viñetas puntuales si hay especificaciones. Vocabulario técnico gamer refinado. Mínimo 4 párrafos completos.
    4. PALABRAS CLAVE DE IMAGEN: Escribe un único término conceptual muy corto y conciso en inglés, SIN COMAS, ideal para buscar un fondo de pantalla del tema en internet. (Ejemplo: 'nvidia rtx GPU concept' o 'futuristic hardware design'). No mezcles múltiples frases separadas por comas.
    
    RESPONDE EXCLUSIVAMENTE EN EL SIGUIENTE FORMATO JSON PLANO (Sin markdown ```json):
    {{
      "titulo": "Título profesional aquí",
      "resumen": "Resumen corto e intrigante aquí.",
      "cuerpo": "Contenido del cuerpo formateado en HTML limpio.",
      "categoria": "{categoria}",
      "termino_busqueda_imagen": "termino corto en ingles sin comas aqui"
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=seguridad, 
                response_mime_type="application/json"
            )
        )
        articulo_ia = json.loads(response.text)
    except Exception as e:
        print(f"❌ ERROR CON GEMINI: {e}")
        sys.exit(1)

    print("🖼️ Fase 3: Buscando y consolidando imágenes de alta relevancia...")
    
    # 1. Extraer fotos de tus enlaces manuales (lo cual funcionó de maravilla)
    opciones_imagenes = extraer_imagenes_de_enlaces(enlaces_manuales)
    
    # 2. Intentar buscar en DuckDuckGo saneando el término (quitando comas si la IA se equivoca)
    palabras_clave_ia = articulo_ia.get("termino_busqueda_imagen", tema)
    if "," in palabras_clave_ia:
        palabras_clave_ia = palabras_clave_ia.split(",")[0].strip()
        
    print(f"🔎 Buscando alternativas de apoyo en la web usando el motor de IA: '{palabras_clave_ia}'...")
    
    try:
        with DDGS() as ddgs:
            img_results = list(ddgs.images(f"{palabras_clave_ia} gaming wallpaper", max_results=15))
            for img in img_results:
                url = img.get('image')
                if url and url.startswith("http"):
                    if not any(x in url.lower() for x in ["thumbnail", "icon", "avatar", "logo", "loader", "sprite"]):
                        if url not in opciones_imagenes: 
                            opciones_imagenes.append(url)
                if len(opciones_imagenes) >= 5:
                    break
    except Exception as e:
        print(f"⚠️ Nota: Buscador de imágenes web omitido ({e}). Dependeremos de los enlaces del usuario.")
    
    # Imágenes de respaldo universales
    imagenes_respaldo = [
        "[https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200](https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200)",
        "[https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=1200](https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=1200)",
        "[https://images.unsplash.com/photo-1538481199705-c710c4e965fc?q=80&w=1200](https://images.unsplash.com/photo-1538481199705-c710c4e965fc?q=80&w=1200)"
    ]
    for img_res in imagenes_respaldo:
        if len(opciones_imagenes) >= 3: break
        if img_res not in opciones_imagenes:
            opciones_imagenes.append(img_res)

    opciones_imagenes = opciones_imagenes[:3]

    borrador_data = {
        "titulo": articulo_ia.get("titulo", "Artículo de Tecnología"),
        "resumen": articulo_ia.get("resumen", "Previa del artículo."),
        "cuerpo": articulo_ia.get("cuerpo", ""),
        "categoria": categoria,
        "imagenes_candidatas": opciones_imagenes
    }
    
    with open(archivo_borrador, "w", encoding="utf-8") as f:
        json.dump(borrador_data, f, ensure_ascii=False, indent=2)
        
    print("\n" + "="*60)
    print("🎉 ¡SÚPER BORRADOR GENERADO CON ÉXITO!")
    print(f"📝 Título: {borrador_data['titulo']}")
    print(f"🔑 Término IA usado para fotos: '{palabras_clave_ia}'")
    print("="*60)
    print("🖼️ REVISA ESTAS 3 URLS DIFERENTES EN TU NAVEGADOR:")
    print(f" Opc [1]: {opciones_imagenes[0]}")
    print(f" Opc [2]: {opciones_imagenes[1]}")
    print(f" Opc [3]: {opciones_imagenes[2]}")
    print("="*60)
    print("💡 Todo listo. Ahora ejecuta el flujo en GitHub seleccionando '2_publicar_borrador'.")

# =====================================================================
# 🚀 FASE 2: APROBAR Y PUBLICAR EL BORRADOR EN PRODUCCIÓN
# =====================================================================
elif accion == "2_publicar_borrador":
    if not os.path.exists(archivo_borrador):
        print("❌ ERROR: No hay ningún borrador creado previamente. Corre primero la acción '1_generar_borrador'.")
        sys.exit(1)
        
    with open(archivo_borrador, "r", encoding="utf-8") as f:
        borrador = json.load(f)
        
    idx_foto = int(imagen_ok) - 1
    if idx_foto < 0 or idx_foto > 2: idx_foto = 0
    imagen_final = borrador["imagenes_candidatas"][idx_foto]
    
    slug = re.sub(r'[^a-z0-9]+', '-', borrador["titulo"].lower()).strip('-')
    from datetime import datetime
    
    nuevo_articulo = {
        "id": f"art-{slug}",
        "titulo": borrador["titulo"],
        "resumen": borrador["resumen"],
        "cuerpo": borrador["cuerpo"],
        "categoria": borrador["categoria"],
        "imagen": imagen_final,
        "fecha": datetime.now().strftime("%d %b, %Y"),
        "enlace": enlaces_manuales.split(",")[0].strip() if enlaces_manuales else "[https://kazokugaming.com](https://kazokugaming.com)"
    }
    
    articulos_lista = []
    if os.path.exists(archivo_oficial):
        try:
            with open(archivo_oficial, "r", encoding="utf-8") as f:
                articulos_lista = json.load(f)
                if isinstance(articulos_lista, dict):
                    articulos_lista = articulos_lista.get("articulos", [])
        except Exception:
            articulos_lista = []
            
    articulos_lista.insert(0, nuevo_articulo)
    
    with open(archivo_oficial, "w", encoding="utf-8") as f:
        json.dump(articulos_lista, f, ensure_ascii=False, indent=2)
        
    if os.path.exists(archivo_borrador):
        os.remove(archivo_borrador)
        
    print(f"🚀 ¡ÉXITO TOTAL! El artículo '{nuevo_articulo['titulo']}' ya está en producción con la imagen seleccionada.")
