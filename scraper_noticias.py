import os
import sys
import json
import time
import feedparser
from datetime import datetime, timedelta
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: NOTICIAS (SISTEMA DE SEGURIDAD PARA JSON) ===")

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

# 📡 RED DE MEDIOS (6 Fuentes de rastreo simultáneo)
rss_urls = [
    "https://es.ign.com/feed.xml",
    "https://www.eurogamer.es/feed",
    "https://www.levelup.com/rss/noticias",
    "https://vandal.elespanol.com/xml.cgi",
    "https://www.3djuegos.com/noticias.xml",
    "https://www.gamereactor.es/rss/rss.php"
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
pool_acumulado = []
urls_existentes = set()
limite_5dias = datetime.now() - timedelta(days=5)

# 🧠 1. RECUPERAR HISTORIAL PREVIO (Filtro de 5 días)
if os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos_viejos = json.load(f)
            
            # Extraemos todas las noticias anteriores en un solo grupo plano
            noticias_anteriores = []
            if datos_viejos.get("destacada") and datos_viejos["destacada"].get("titulo"):
                noticias_anteriores.append(datos_viejos["destacada"])
            if datos_viejos.get("secundarias"):
                noticias_anteriores.extend(datos_viejos["secundarias"])
                
            for n in noticias_anteriores:
                if "fecha" in n and "enlace" in n:
                    try:
                        fecha_n = datetime.fromisoformat(n["fecha"])
                        # Si tiene menos de 5 días, se queda en el sistema
                        if fecha_n > limite_5dias:
                            pool_acumulado.append(n)
                            urls_existentes.add(n["enlace"])
                    except:
                        pass
    except Exception as e:
        print(f"⚠️ Archivo JSON corrupto o vacío, se creará uno nuevo limpio. ({e})")

# 🌐 2. BUSCAR INFORMACIÓN EN LA RED
nuevas_entradas = []
for url in rss_urls:
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:4]:
            if entry.link not in urls_existentes:
                nuevas_entradas.append(entry)
    except Exception as e:
        print(f"⚠️ Error leyendo fuente {url}: {e}")

# Limitamos a un máximo de 6 noticias nuevas por ejecución para cuidar la cuota de la API
nuevas_entradas = nuevas_entradas[:6]

if not nuevas_entradas:
    print("✅ No hay noticias nuevas en las redes. Manteniendo el catálogo de 5 días intacto.")
    if pool_acumulado:
        pool_acumulado.sort(key=lambda x: x.get("fecha", ""), reverse=True)
        estructura_final = {
            "destacada": pool_acumulado[0],
            "secundarias": pool_acumulado[1:]
        }
        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(estructura_final, f, ensure_ascii=False, indent=2)
    sys.exit(0)

# ✍️ 3. REDACCIÓN CON IA (Generamos las crónicas nuevas)
timestamp_base = int(time.time())

for idx, entrada in enumerate(nuevas_entradas):
    print(f"📝 [{idx+1}/{len(nuevas_entradas)}] Redactando: {entrada.title}")
    
    prompt = f"""
    Actúa como un editor jefe y redactor experto en videojuegos. Tu tarea es analizar la siguiente noticia y reescribir la información y la sinopsis desde cero, creando un artículo completamente nuevo.
    
    Debes utilizar un tono de "gaming moderno", dinámico y atractivo. Es estrictamente necesario que realices una curación editorial original para evitar cualquier problema de copyright con la fuente. No copies frases literales.
    
    Título fuente: {entrada.title}
    
    Devuelve EXCLUSIVAMENTE un objeto JSON estructurado así, sin texto adicional ni formato markdown extra:
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
        
        data_redactada["id"] = f"noticia-{timestamp_base}-{idx}"
        data_redactada["enlace"] = entrada.link
        data_redactada["imagen"] = obtener_imagen(entrada)
        data_redactada["fecha"] = datetime.now().isoformat()
        
        pool_acumulado.append(data_redactada)
        
    except Exception as e:
        print(f"⚠️ No se pudo procesar esta entrada: {e}")
        
    time.sleep(12)

# 💾 4. RE-ORDENAR TODO Y ESCRIBIR EL ARCHIVO FINAL
# Ordenamos todo el pool combinado (lo viejo + lo nuevo) de más reciente a más antiguo
pool_acumulado.sort(key=lambda x: x.get("fecha", ""), reverse=True)

# Creamos la estructura limpia sin anidaciones corruptas
noticias_actualizadas = {
    "destacada": pool_acumulado[0] if len(pool_acumulado) > 0 else {},
    "secundarias": pool_acumulado[1:] if len(pool_acumulado) > 1 else []
}

# Guardado seguro en disco
with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(noticias_actualizadas, f, ensure_ascii=False, indent=2)

print(f"✅ Sincronización completada. Archivo noticias.json re-estructurado con éxito sin errores.")
