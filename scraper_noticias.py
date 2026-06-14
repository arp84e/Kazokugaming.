import os
import sys
import json
import time
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: NOTICIAS CON AUTO-CORRECTOR MULTIMODAL ===")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

seguridad_permisiva = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

# 📡 RED DE MEDIOS (Fuentes de rastreo simultáneo)
rss_urls = [
    "https://es.ign.com/feed.xml",
    "https://www.eurogamer.es/feed",
    "https://www.levelup.com/rss/noticias",
    "https://vandal.elespanol.com/xml.cgi",
    "https://www.3djuegos.com/noticias.xml",
    "https://www.gamereactor.es/rss/rss.php"
]

def obtener_imagen(entrada):
    """ Intenta extraer la URL original de la imagen desde el feed RSS """
    html_content = ""
    if 'summary' in entrada:
        html_content += entrada.summary
    if 'content' in entrada:
        for c in entrada.content:
            html_content += c.value
            
    if html_content:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            img_tag = soup.find('img')
            if img_tag and img_tag.get('src'):
                src = img_tag['src']
                if not any(x in src.lower() for x in ['pixel', 'analytics', 'avatar', 'logo', 'profile']):
                    return src
        except:
            pass

    if 'media_content' in entrada and len(entrada.media_content) > 0:
        for media in entrada.media_content:
            url = media.get('url', '')
            if url and not any(x in url.lower() for x in ['avatar', 'logo', 'profile', 'pixel', 'author']):
                return url
        return entrada.media_content[0]['url']
        
    if 'media_thumbnail' in entrada and len(entrada.media_thumbnail) > 0:
        return entrada.media_thumbnail[0]['url']
        
    if 'links' in entrada:
        for link in entrada.links:
            if 'image' in link.get('type', ''):
                return link.href
                
    return ""

def pedir_keywords_fallback(titulo_noticia):
    """ Genera palabras clave de respaldo basadas únicamente en el título si la imagen falló por completo """
    prompt_texto = f"""
    Basándote en este título de noticia gamer/geek: '{titulo_noticia}',
    genera 2 palabras clave en INGLÉS separadas por coma que describan la temática (ej: "dragon,throne" o "cyberpunk,cyborg").
    Devuelve estrictamente un objeto JSON:
    {{
      "palabras_clave": "terminos_en_ingles"
    }}
    """
    try:
        res = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt_texto,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(res.text)
        kw = data.get("palabras_clave", "gaming").replace(" ", "")
        return f"https://loremflickr.com/800/450/{kw}"
    except:
        return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"

def validar_y_corregir_imagen(url_imagen, titulo_noticia):
    """ 
    Usa la visión de Gemini para validar la imagen actual. 
    Si no corresponde, pide palabras clave y devuelve una imagen dinámica de reemplazo.
    """
    if not url_imagen or "images.unsplash.com" in url_imagen:
        return pedir_keywords_fallback(titulo_noticia)
        
    try:
        print(f"👁️ Analizando visualmente: {url_imagen[:60]}...")
        img_resp = requests.get(url_imagen, timeout=6)
        if img_resp.status_code == 200:
            mime_type = img_resp.headers.get('Content-Type', 'image/jpeg')
            if 'image' in mime_type:
                img_part = types.Part.from_bytes(data=img_resp.content, mime_type=mime_type)
                
                prompt_vista = f"""
                Analiza si esta imagen corresponde de forma real y directa al tema de esta noticia: '{titulo_noticia}'.
                
                Debes responder EXCLUSIVAMENTE con un objeto JSON estructurado exactamente así:
                {{
                  "valido": false,
                  "palabras_clave": "2_o_3_terminos_en_ingles_separados_por_comas"
                }}
                
                Reglas críticas:
                1. Si la imagen NO coincide con el título de la noticia de forma coherente (ej: sale la cara del actor de Dr. House para una noticia sobre la serie 'House of the Dragon', sale un logo genérico del medio periodístico, publicidad, o un avatar del redactor), marca "valido": false. En "palabras_clave" escribe 2 términos en INGLÉS muy específicos sobre la serie/juego (ej: "dragon,throne" o "eldenring,armor") para usarlos en un buscador de stock.
                2. Si la imagen es correcta y guarda relación directa con la noticia, marca "valido": true y deja "palabras_clave": "".
                """
                
                res_verif = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=[img_part, prompt_vista],
                    config=types.GenerateContentConfig(
                        safety_settings=seguridad_permisiva,
                        response_mime_type="application/json"
                    )
                )
                
                data_verif = json.loads(res_verif.text)
                if data_verif.get("valido") == True:
                    print("✅ Imagen aprobada por la IA.")
                    return url_imagen
                else:
                    kw = data_verif.get("palabras_clave", "gaming").replace(" ", "")
                    nueva_url = f"https://loremflickr.com/800/450/{kw}"
                    print(f"🚫 Imagen RECHAZADA. Reemplazada por términos clave: {nueva_url}")
                    return nueva_url
    except Exception as e:
        print(f"⚠️ Error en validación visual ({e}). Buscando fallback automatizado...")
        
    return pedir_keywords_fallback(titulo_noticia)


archivo_json = 'noticias.json'
pool_acumulado = []
urls_existentes = set()
limite_5dias = datetime.now() - timedelta(days=5)

# 🧠 1. RECUPERAR HISTORIAL PREVIO (Filtro de 5 días)
if os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos_viejos = json.load(f)
            
            noticias_anteriores = []
            if datos_viejos.get("destacada") and datos_viejos["destacada"].get("titulo"):
                noticias_anteriores.append(datos_viejos["destacada"])
            if datos_viejos.get("secundarias"):
                noticias_anteriores.extend(datos_viejos["secundarias"])
                
            for n in noticias_anteriores:
                if "fecha" in n and "enlace" in n:
                    try:
                        fecha_n = datetime.fromisoformat(n["fecha"])
                        if fecha_n > limite_5dias:
                            pool_acumulado.append(n)
                            urls_existentes.add(n["enlace"])
                    except:
                        pass
    except Exception as e:
        print(f"⚠️ Archivo JSON corrupto o vacío, comenzando limpio. ({e})")

# 🔮 2. FASE DE AUTO-CORRECCIÓN: LIMPIAR LAS NOTICIAS QUE YA ESTÁN PUBLICADAS ACTUALMENTE
if pool_acumulado:
    print(f"\n🔮 [Fase de Corrección] Analizando las {len(pool_acumulado)} noticias publicadas en la web...")
    for noticia in pool_acumulado:
        img_actual = noticia.get("imagen", "")
        # Solo analizamos si no ha sido procesada previamente por LoremFlickr
        if "loremflickr.com" not in img_actual:
            nueva_img = validar_y_corregir_imagen(img_actual, noticia.get("titulo", ""))
            noticia["imagen"] = nueva_img
            time.sleep(2) # Pausa de cortesía entre llamadas

# 🌐 3. BUSCAR INFORMACIÓN NUEVA EN LA RED
nuevas_entradas = []
for url in rss_urls:
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:4]:
            if entry.link not in urls_existentes:
                nuevas_entradas.append(entry)
    except Exception as e:
        print(f"⚠️ Error leyendo fuente {url}: {e}")

nuevas_entradas = nuevas_entradas[:6]

# Si no hay noticias nuevas en este ciclo, guardamos las correcciones hechas en la base de datos y finalizamos
if not nuevas_entradas:
    print("✅ No hay noticias nuevas hoy. Guardando las correcciones de imágenes efectuadas en la hemeroteca.")
    if pool_acumulado:
        pool_acumulado.sort(key=lambda x: x.get("fecha", ""), reverse=True)
        estructura_final = {
            "destacada": pool_acumulado[0],
            "secundarias": pool_acumulado[1:]
        }
        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(estructura_final, f, ensure_ascii=False, indent=2)
    sys.exit(0)

# ✍️ 4. REDACCIÓN CON IA (Para las entradas nuevas de hoy)
timestamp_base = int(time.time())

for idx, entrada in enumerate(nuevas_entradas):
    print(f"\n📝 [{idx+1}/{len(nuevas_entradas)}] Redactando nueva crónica: {entrada.title}")
    
    prompt = f"""
    Actúa como un editor jefe y redactor experto en videojuegos. Analiza la siguiente noticia y reescribe la información desde cero.
    Usa un tono "gaming moderno", dinámico y atractivo. Evita copiar frases literales de la fuente.
    
    Título fuente: {entrada.title}
    
    Devuelve EXCLUSIVAMENTE un objeto JSON estructurado así, sin texto adicional ni markdown:
    {{
      "categoria": "Actualidad Gaming",
      "titulo": "Titular potente, llamativo y 100% original",
      "resumen": "Sinopsis reescrita y atractiva de un párrafo corto.",
      "contenido_completo": "<p>Cobertura detallada, redactada con voz propia en formato HTML, compuesta por dos párrafos bien estructurados.</p>"
    }}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=seguridad_permisiva, 
                response_mime_type="application/json"
            )
        )
        data_redactada = json.loads(response.text)
        
        # Obtener imagen del RSS y pasarla por el validador/corrector inteligente
        url_original = obtener_imagen(entrada)
        url_final_imagen = validar_y_corregir_imagen(url_original, data_redactada.get("titulo"))

        data_redactada["id"] = f"noticia-{timestamp_base}-{idx}"
        data_redactada["enlace"] = entrada.link
        data_redactada["imagen"] = url_final_imagen
        data_redactada["fecha"] = datetime.now().isoformat()
        
        pool_acumulado.append(data_redactada)
        
    except Exception as e:
        print(f"⚠️ No se pudo procesar esta entrada: {e}")
        
    time.sleep(10)

# 💾 5. RE-ORDENAR TODO Y ESCRIBIR EL ARCHIVO FINAL SANEADO
pool_acumulado.sort(key=lambda x: x.get("fecha", ""), reverse=True)

noticias_actualizadas = {
    "destacada": pool_acumulado[0] if len(pool_acumulado) > 0 else {},
    "secundarias": pool_acumulado[1:] if len(pool_acumulado) > 1 else []
}

with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(noticias_actualizadas, f, ensure_ascii=False, indent=2)

print(f"✅ Sincronización completada. ¡Historial e imágenes completamente saneadas!")
