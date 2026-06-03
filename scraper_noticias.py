import os
import sys
import json
import time
import feedparser
from datetime import datetime, timedelta
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: NOTICIAS MULTIFUENTE ===")

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

# 📡 1. LISTA DE FUENTES (Puedes agregar más enlaces RSS aquí)
rss_urls = [
    "https://es.ign.com/feed.xml",
    "https://www.eurogamer.es/feed",
    "https://www.levelup.com/rss/noticias"
]

def obtener_imagen(entrada):
    if 'media_content' in entrada and len(entrada.media_content) > 0:
        return entrada.media_content[0]['url']
    if 'media_thumbnail' in entrada and len(entrada.media_thumbnail) > 0:
        return entrada.media_thumbnail[0]['url']
    if 'links' in entrada:
        for link in entrada.links:
            if 'image' in link.get('type', ''):
                return link.href
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"

archivo_json = 'noticias.json'
datos_finales = {"destacada": {}, "secundarias": []}
historial_valido = []
urls_existentes = set()
limite_72h = datetime.now() - timedelta(days=3)

# 🧠 2. SISTEMA DE MEMORIA: Recuperar noticias de los últimos 3 días
if os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos_viejos = json.load(f)
            
            # Unificamos todas las noticias anteriores (destacada + secundarias)
            todas_viejas = datos_viejos.get("secundarias", [])
            if datos_viejos.get("destacada"):
                todas_viejas.insert(0, datos_viejos["destacada"])
                
            for n in todas_viejas:
                if "fecha" in n:
                    try:
                        fecha_n = datetime.fromisoformat(n["fecha"])
                        # Si la noticia tiene menos de 3 días, la salvamos del borrado
                        if fecha_n > limite_72h:
                            historial_valido.append(n)
                            urls_existentes.add(n.get("enlace", ""))
                    except:
                        pass
    except Exception as e:
        print(f"⚠️ Aviso: No se pudo leer el historial anterior ({e})")

# 🌐 3. BUSCAR NUEVAS NOTICIAS EN TODAS LAS FUENTES
nuevas_entradas = []
for url in rss_urls:
    print(f"Sintonizando antena: {url}")
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]: # Tomamos las 3 más frescas de cada página
            if entry.link not in urls_existentes:
                nuevas_entradas.append(entry)
    except Exception as e:
        print(f"⚠️ Error leyendo {url}: {e}")

# Limitamos a procesar un máximo de 4 noticias nuevas por ejecución 
# para proteger tu cuota gratuita de la API de Gemini
nuevas_entradas = nuevas_entradas[:4]

if not nuevas_entradas:
    print("✅ No hay noticias nuevas en la web. Se mantendrá el catálogo actual de 72 horas.")
    if historial_valido:
        datos_finales["destacada"] = historial_valido.pop(0) # La más reciente vuelve a ser destacada
        datos_finales["secundarias"] = historial_valido
        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(datos_finales, f, ensure_ascii=False, indent=2)
    sys.exit(0)

# ✍️ 4. REDACCIÓN CON INTELIGENCIA ARTIFICIAL
# La noticia nueva #1 será la Gran Destacada
noticia_origen = nuevas_entradas[0]
print(f"🗞️ Redactando Nueva Destacada: {noticia_origen.title}")

prompt_destacada = f"""
Actúa como un editor principal de videojuegos. Redacta un artículo basado en:
Título: {noticia_origen.title}
Devuelve UNICAMENTE un objeto JSON válido con esta estructura:
{{
  "id": "dest-{int(time.time())}",
  "categoria": "Reporte Principal",
  "titulo": "Título potente y atractivo",
  "resumen": "Resumen de máximo 2 líneas.",
  "contenido_completo": "<p>Escribe aquí 2 párrafos detallando la noticia en formato HTML.</p>",
  "enlace": "{noticia_origen.link}",
  "fecha": "{datetime.now().isoformat()}"
}}
"""

try:
    res_dest = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_destacada,
        config=types.GenerateContentConfig(safety_settings=seguridad_permisiva, response_mime_type="application/json")
    )
    datos_dest = json.loads(res_dest.text)
    datos_dest["imagen"] = obtener_imagen(noticia_origen)
    datos_finales["destacada"] = datos_dest
except Exception as e:
    print(f"⚠️ Error en destacada: {e}")
    if historial_valido:
        datos_finales["destacada"] = historial_valido.pop(0)

time.sleep(15) # Pausa estratégica

# Redactar el resto de las noticias nuevas como secundarias
nuevas_secundarias = []
for i in range(1, len(nuevas_entradas)):
    noticia_sec = nuevas_entradas[i]
    print(f"📝 Redactando Secundaria: {noticia_sec.title}")
    
    prompt_sec = f"""
    Resume esta noticia para una tarjeta web rápida:
    Título: {noticia_sec.title}
    Devuelve UNICAMENTE un objeto JSON válido con esta estructura:
    {{
      "id": "sec-{int(time.time())}-{i}",
      "categoria": "Actualidad",
      "titulo": "Título directo",
      "resumen": "Un resumen de máximo 3 líneas.",
      "enlace": "{noticia_sec.link}",
      "fecha": "{datetime.now().isoformat()}"
    }}
    """
    try:
        res_sec = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_sec,
            config=types.GenerateContentConfig(safety_settings=seguridad_permisiva, response_mime_type="application/json")
        )
        datos_sec = json.loads(res_sec.text)
        datos_sec["imagen"] = obtener_imagen(noticia_sec)
        nuevas_secundarias.append(datos_sec)
    except Exception as e:
        print(f"⚠️ Error en secundaria {i}: {e}")
        
    time.sleep(15)

# 💾 5. FUSIONAR Y GUARDAR
# Juntamos las noticias recién creadas con el historial válido de los últimos 3 días
datos_finales["secundarias"] = nuevas_secundarias + historial_valido

with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(datos_finales, f, ensure_ascii=False, indent=2)

print(f"✅ Catálogo guardado. Total en pantalla: 1 destacada y {len(datos_finales['secundarias'])} crónicas recientes.")
