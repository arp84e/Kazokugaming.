import os
import sys
import json
import time
import re
from datetime import datetime, timedelta
import feedparser
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT ===")

# Validar que las variables de entorno existan
api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")

if not api_key:
    print("❌ ERROR CRÍTICO: No se encontró GEMINI_API_KEY. Verifica los Secrets de GitHub.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# Variables globales para fechas
hoy = datetime.now()
meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# ==========================================
# FILTROS DE SEGURIDAD GLOBALES (CRÍTICO PARA JUEGOS)
# Evita que la IA se bloquee al leer sobre juegos de acción o shooters
# ==========================================
seguridad_permisiva = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

# ==========================================
# TAREA 1: SISTEMA DE NOTICIAS
# ==========================================
print("\n--- EJECUTANDO TAREA 1: NOTICIAS ---")
archivo_json = 'noticias.json'
historial = []

if os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'destacada' in data: historial.append(data['destacada'])
            if 'secundarias' in data: historial.extend(data['secundarias'])
    except: pass

fecha_limite = datetime.now() - timedelta(days=3)
noticias_validas = []
enlaces_guardados = set()

for noticia in historial:
    fecha_str = noticia.get('fecha', datetime.now().isoformat())
    try: fecha_obj = datetime.fromisoformat(fecha_str)
    except: fecha_obj = datetime.now()
        
    if fecha_obj > fecha_limite:
        noticia['fecha'] = fecha_obj.isoformat()
        noticias_validas.append(noticia)
        enlaces_guardados.add(noticia.get('enlace', ''))

feed = feedparser.parse("https://feeds.feedburner.com/ign/games-all")
nuevas_entradas = [e for e in feed.entries if e.link not in enlaces_guardados][:3]
noticias_totales = noticias_validas

if nuevas_entradas:
    print(f">> Procesando {len(nuevas_entradas)} noticias nuevas...")
    textos = ""
    for e in nuevas_entradas:
        img = ""
        if 'media_content' in e and len(e.media_content) > 0: img = e.media_content[0]['url']
        elif 'media_thumbnail' in e and len(e.media_thumbnail) > 0: img = e.media_thumbnail[0]['url']
        textos += f"Título: {e.title}\nResumen: {e.summary}\nEnlace: {e.link}\nImagen oficial: {img}\n\n"
        
    prompt = f"""Eres el redactor principal de KazokuGaming, un medio de videojuegos conocido por su estilo directo, entusiasta y altamente enfocado en el rendimiento técnico (tanto de PC como de consolas).
    Tu tarea es leer la siguiente información y redactar artículos COMPLETAMENTE NUEVOS y ORIGINALES.
    
    Reglas estrictas para evitar plagio:
    1. NO traduzcas, no parafrasees de forma simple y no copies la estructura original. 
    2. Usa la información solo como "fuente de datos" bruta. Construye la noticia desde cero, aportando una introducción con gancho, un análisis crítico del anuncio y una conclusión.
    3. Añade tu propio toque editorial. Si la noticia trata sobre un juego nuevo o hardware, menciona libremente tus expectativas sobre tasas de cuadros, requisitos técnicos, rendimiento gráfico o impacto en la industria.
    4. Usa etiquetas HTML (<p>, <h3>, <strong>, <ul>) dentro del campo 'contenido_completo' para estructurar bien la lectura.

    Genera un JSON con una lista llamada "nuevas_noticias". Formato estricto: {{"nuevas_noticias": [ {{"categoria": "...", "titulo": "...", "resumen": "...", "contenido_completo": "...", "imagen": "URL", "enlace": "..."}} ] }}
    
    Información fuente a analizar (solo para extraer datos objetivos):\n{textos}"""
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                safety_settings=seguridad_permisiva # Añadido filtro
            )
        )
        
        texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
        noticias_ia = json.loads(texto_limpio).get("nuevas_noticias", [])
        
        for i, n in enumerate(noticias_ia):
            n['fecha'] = datetime.now().isoformat()
            n['id'] = f"not_{int(time.time())}_{i}"
        noticias_totales = noticias_ia + noticias_validas
    except Exception as e: 
        print("❌ Error procesando noticias:", e)

if noticias_totales:
    try:
        with open('noticias.json', 'w', encoding='utf-8') as f:
            json.dump({"destacada": noticias_totales[0], "secundarias": noticias_totales[1:]}, f, ensure_ascii=False, indent=2)
        print("✅ noticias.json actualizado correctamente.")
    except Exception as e:
        print("❌ Error al guardar noticias.json:", e)


# ==========================================
# FUNCIÓN AUXILIAR: BUSCADOR DE IMÁGENES (RAWG)
# ==========================================
def buscar_portada_juego(titulo_juego):
    if not rawg_key: return ""
    try:
        url = f"https://api.rawg.io/api/games?key={rawg_key}&search={titulo_juego}&page_size=1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("results"): return data["results"][0].get("background_image", "")
    except Exception: pass
    return ""


# ==========================================
# TAREA 2: SISTEMA DE TELEMETRÍA (ANÁLISIS DE JUEGOS)
# ==========================================
print("\n--- EJECUTANDO TAREA 2: TELEMETRÍA (ANÁLISIS MANUAL) ---")

# 🎮 TU LISTA PERSONALIZADA DE JUEGOS
juegos_manuales = [
    {"titulo": "Hollow Knight: Silksong", "fecha": "Por confirmar", "plataformas": "PC, Switch, Xbox, PS5"},
    {"titulo": "Grand Theft Auto VI", "fecha": "Otoño 2025", "plataformas": "PS5, Xbox Series X/S"},
    {"titulo": "DOOM: The Dark Ages", "fecha": "2025", "plataformas": "PC, PS5, Xbox Series X/S"},
    {"titulo": "Metal Gear Solid Delta: Snake Eater", "fecha": "2024 / 2025", "plataformas": "PC, PS5, Xbox"}
]

estructura_final = {
    "juegos": []
}

print(f">> Procesando {len(juegos_manuales)} títulos en Telemetría...")

for juego in juegos_manuales:
    titulo = juego["titulo"]
    print(f"-> Analizando hardware y redactando datos para: {titulo}...")
    
    prompt_telemetria = f"""Eres el analista técnico principal de KazokuGaming.
    Analiza el juego '{titulo}'.
    Devuelve ÚNICAMENTE un JSON válido. NO uses bloques de código markdown.
    
    Estructura OBLIGATORIA:
    {{
      "sinopsis": "Un párrafo técnico y original (4-5 líneas) sobre el motor gráfico y mecánicas.",
      "requisitos": {{
        "minimos": ["Procesador: ...", "Gráficos: ...", "Memoria: ...", "Almacenamiento: ..."],
        "recomendados": ["Procesador: ...", "Gráficos: ...", "Memoria: ...", "Almacenamiento: ..."]
      }}
    }}
    """
    
    datos_ia = {
        "sinopsis": "Análisis técnico en desarrollo.",
        "requisitos": {"minimos": [], "recomendados": []}
    }
    
    try:
        respuesta_ia = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_telemetria,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                safety_settings=seguridad_permisiva
            )
        )
        
        texto_crudo = respuesta_ia.text
        match = re.search(r'\{.*\}', texto_crudo, re.DOTALL)
        
        if match:
            texto_json = match.group(0)
            datos_ia = json.loads(texto_json)
            print(f"   [+] Análisis extraído con éxito.")
        else:
            print(f"   [!] La IA no devolvió un formato reconocible.")
            datos_ia["sinopsis"] = "⚠️ Fallo de formato: La IA no estructuró los datos correctamente."
            
    except Exception as e:
        # AQUÍ ESTÁ LA MAGIA: Capturamos el error real y lo enviamos a tu web
        error_str = str(e).replace('"', "'")
        print(f"   [!] Error técnico al procesar {titulo}: {error_str}")
        datos_ia["sinopsis"] = f"⚠️ ERROR DEL SISTEMA: {error_str}"

    imagen_url = buscar_portada_juego(titulo)
    id_juego = titulo.lower().replace(":", "").replace(" ", "-").replace("/", "-")

    estructura_final["juegos"].append({
        "id": id_juego,
        "titulo": titulo,
        "fecha": juego["fecha"],
        "plataformas": juego["plataformas"],
        "sinopsis": datos_ia.get("sinopsis", "Análisis técnico en desarrollo."),
        "requisitos": datos_ia.get("requisitos", {"minimos": [], "recomendados": []}),
        "imagen": imagen_url
    })
    
    print("   ... Pausa de seguridad (5s) ...")
    time.sleep(5)

try:
    with open('lanzamientos.json', 'w', encoding='utf-8') as f:
        json.dump(estructura_final, f, ensure_ascii=False, indent=2)
    print("\n✅ Base de datos de Telemetría (lanzamientos.json) actualizada correctamente.")
except Exception as e:
    print("\n❌ Error escribiendo lanzamientos.json:", e)

print("=== KAZOKUBOT FINALIZADO CORRECTAMENTE ===")
