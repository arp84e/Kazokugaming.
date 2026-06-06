import os
import sys
import json
import time
import feedparser
from datetime import datetime, timedelta
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: NOTICIAS RED EXTENDIDA (5 DÍAS DE RETENCIÓN) ===")

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

# 📡 RED DE MEDIOS (6 Fuentes de rastreo)
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
historial_valido = []
urls_existentes = set()

# 🧠 CAMBIO AQUÍ: Extendemos el límite de memoria a 5 días exactos (120 horas)
limite_5dias = datetime.now() - timedelta(days=5)

# SISTEMA DE MEMORIA PASADA
if os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos_viejos = json.load(f)
            
            todas_viejas = datos_viejos.get("secundarias", [])
            if datos_viejos.get("destacada") and datos_viejos["destacada"].get("titulo"):
                todas_viejas.insert(0, datos_viejos["destacada"])
                
            for n in todas_viejas:
                if "fecha" in n:
                    try:
                        fecha_n = datetime.fromisoformat(n["fecha"])
                        # Retenemos todo lo que tenga menos de 5 días
                        if fecha_n > limite_5dias:
                            historial_valido.append(n)
                            urls_existentes.add(n.get("enlace", ""))
                    except:
                        pass
    except Exception as e:
        print(f"⚠️ Aviso de lectura del archivo base: {e}")

# 🌐 ESCANEO GLOBAL DE ENTRADAS NEW
nuevas_entradas = []
for url in rss_urls:
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:4]:
            if entry.link not in urls_existentes:
                nuevas_entradas.append(entry)
    except Exception as e:
        print(f"⚠️ Omisión temporal de fuente por error de red: {e}")

# Configuración de procesamiento balanceado por ciclo
NUEVAS_SECUNDARIAS_OBJETIVO = 10
MAX_PROCESAR_NUEVAS = 1 + NUEVAS_SECUNDARIAS_OBJETIVO
nuevas_entradas = nuevas_entradas[:MAX_PROCESAR_NUEVAS]

if not nuevas_entradas:
    print("✅ No hay novedades críticas en las redes. Manteniendo historial activo de 5 días.")
    if historial_valido:
        datos_finales["destacada"] = historial_valido.pop(0)
        datos_finales["secundarias"] = historial_valido
        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(datos_finales, f, ensure_ascii=False, indent=2)
    sys.exit(0)

# ✍️ REDACCIÓN PRINCIPAL (Noticia Destacada)
noticia_origen = nuevas_entradas[0]
print(f"🗞️ Creando Reporte Principal: {noticia_origen.title}")

# Guardamos un ID basado en timestamp único
timestamp_id = int(time.time())

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
    print(f"❌ Desviación en flujo principal: {e}")
    if historial_valido:
        datos_finales["destacada"] = historial_valido.pop(0)

time.sleep(12)

# 📝 GENERACIÓN DEL BLOQUE DE NOTICIAS SECUNDARIAS
nuevas_secundarias = []
for i in range(1, len(nuevas_entradas)):
    noticia_sec = nuevas_entradas[i]
    print(f"📝 Redactando Tarjeta de Actualidad [{i}/{len(nuevas_entradas)-1}]: {noticia_sec.title}")
    
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
        nuevas_secundarias.append(datos_sec)
    except Exception as e:
        print(f"⚠️ Salto de registro secundario por error técnico: {e}")
        
    time.sleep(12)

# CONSOLIDACIÓN FINAL EN EL ARCHIVO DISCO
datos_finales["secundarias"] = nuevas_secundarias + historial_valido

with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(datos_finales, f, ensure_ascii=False, indent=2)

print(f"✅ Sincronización finalizada. Historial ampliado a 5 días con éxito.")
