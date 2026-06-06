import os
import sys
import json
import time
import feedparser
from datetime import datetime, timedelta
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: HEMEROTECA MASIVA (5 DÍAS TOTALES) ===")

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

# 📡 RED DE MEDIOS AMPLIA
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
datos_finales = {"destacada": {}, "secundarias": []}
historial_acumulado = []
urls_existentes = set()
limite_5dias = datetime.now() - timedelta(days=5)

# 🧠 1. MEMORIA DE ACUMULACIÓN: Recuperamos ABSOLUTAMENTE TODO lo que no haya caducado
if os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos_viejos = json.load(f)
            
            # Consolidamos todo el contenido previo para filtrarlo únicamente por tiempo
            pool_previo = datos_viejos.get("secundarias", [])
            if datos_viejos.get("destacada") and datos_viejos["destacada"].get("titulo"):
                pool_previo.insert(0, datos_viejos["destacada"])
                
            for n in pool_previo:
                if "fecha" in n:
                    try:
                        fecha_n = datetime.fromisoformat(n["fecha"])
                        # Si tiene menos de 5 días, se queda en el historial permanentemente
                        if fecha_n > limite_5dias:
                            historial_acumulado.append(n)
                            urls_existentes.add(n.get("enlace", ""))
                    except:
                        pass
    except Exception as e:
        print(f"⚠️ Aviso de lectura: {e}")

# 🌐 2. ESCANEO DE FUENTES EN BUSCA DE EDICIONES NUEVAS
nuevas_entradas = []
for url in rss_urls:
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:4]:
            if entry.link not in urls_existentes:
                nuevas_entradas.append(entry)
    except Exception as e:
        print(f"⚠️ Enlace omitido: {url}")

# Limitamos la IA a redactar un bloque balanceado de hasta 8 noticias frescas por ejecución
nuevas_entradas = nuevas_entradas[:8]

if not nuevas_entradas:
    print("✅ No hay noticias nuevas en la red. Manteniendo las de los últimos 5 días intactas.")
    if historial_acumulado:
        # Re-ordenamos por fecha para asegurar la jerarquía
        historial_acumulado.sort(key=lambda x: x.get("fecha", ""), reverse=True)
        datos_finales["destacada"] = historial_acumulado.pop(0)
        datos_finales["secundarias"] = historial_acumulado
        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(datos_finales, f, ensure_ascii=False, indent=2)
    sys.exit(0)

# ✍️ 3. REDACCIÓN DE NUEVAS CRÓNICAS
timestamp_id = int(time.time())

# Nueva Destacada
noticia_origen = nuevas_entradas[0]
print(f"🗞️ Redactando Destacada: {noticia_origen.title}")
prompt_destacada = f"""
Actúa como un redactor jefe de una revista de videojuegos premium. Redacta una crónica basada en:
Título fuente: {noticia_origen.title}
Devuelve EXCLUSIVAMENTE un objeto JSON válido estructurado así:
{{
  "id": "noticia-{timestamp_id}",
  "categoria": "Reporte Crítico",
  "titulo": "Titular de alto impacto técnico",
  "resumen": "Resumen conciso del acontecimiento.",
  "contenido_completo": "<p>Escribe aquí una cobertura de 2 o 3 párrafos sólidos estructurados con HTML informativo.</p>",
  "enlace": "{noticia_origen.link}",
  "fecha": "{datetime.now().isoformat()}"
}}
"""

nuevas_redactadas = []
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
    print(f"❌ Error en destacada: {e}")

time.sleep(12)

# Nuevas Secundarias
for i in range(1, len(nuevas_entradas)):
    noticia_sec = nuevas_entradas[i]
    print(f"📝 Redactando Secundaria [{i}/{len(nuevas_entradas)-1}]: {noticia_sec.title}")
    
    prompt_sec = f"""
    Sintetiza la novedad para un despliegue rápido en tarjeta web:
    Origen: {noticia_sec.title}
    Devuelve EXCLUSIVAMENTE un objeto JSON válido estructurado así:
    {{
      "id": "noticia-{timestamp_id}-{i}",
      "categoria": "Actualidad Gaming",
      "titulo": "Título directo y con enganche",
      "resumen": "Análisis sintético de un párrafo para lectura veloz.",
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
        nuevas_redactadas.append(datos_sec)
    except Exception as e:
        print(f"⚠️ Error en secundaria: {e}")
    time.sleep(12)

# 💾 4. UNIFICACIÓN Y ORDENAMIENTO ABSOLUTO POR FECHA
# Combinamos todo el historial salvado de 5 días con lo nuevo redactado
todo_el_pool = nuevas_redactadas + historial_acumulado

# Si no pudimos crear una destacada nueva por algún fallo de red, usamos la más reciente disponible
if not datos_finales.get("destacada") and todo_el_pool:
    todo_el_pool.sort(key=lambda x: x.get("fecha", ""), reverse=True)
    datos_finales["destacada"] = todo_el_pool.pop(0)

# El resto va íntegro a las secundarias (sin importar si son 20, 40 o 80 noticias)
todo_el_pool.sort(key=lambda x: x.get("fecha", ""), reverse=True)
datos_finales["secundarias"] = todo_el_pool

with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(datos_finales, f, ensure_ascii=False, indent=2)

print(f"✅ Éxito. Guardadas {len(datos_finales['secundarias']) + 1} noticias en total dentro del rango de los 5 días.")
