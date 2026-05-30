import os
import json
import time
from datetime import datetime, timedelta
import feedparser
import requests  # Asegúrate de que tu entorno/workflow tenga 'requests' instalado
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")  # Tu clave de RAWG

client = genai.Client(api_key=api_key)

# ==========================================
# TAREA 1: SISTEMA DE NOTICIAS (Se mantiene igual)
# ==========================================
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

print("Buscando noticias nuevas...")
feed = feedparser.parse("https://feeds.feedburner.com/ign/games-all")
nuevas_entradas = [e for e in feed.entries if e.link not in enlaces_guardados][:3]
noticias_totales = noticias_validas

if nuevas_entradas:
    textos = ""
    for e in nuevas_entradas:
        img = ""
        if 'media_content' in e and len(e.media_content) > 0: img = e.media_content[0]['url']
        elif 'media_thumbnail' in e and len(e.media_thumbnail) > 0: img = e.media_thumbnail[0]['url']
        textos += f"Título: {e.title}\nResumen: {e.summary}\nEnlace: {e.link}\nImagen oficial: {img}\n\n"
        
    prompt = f"""Eres un periodista de videojuegos. Reescribe estas noticias al español de forma detallada.
    Genera un JSON con una lista llamada "nuevas_noticias".
    REGLA DE IMÁGENES: Usa la URL de la "Imagen oficial" que te doy. Si está vacía, usa obligatoriamente esta URL: https://placehold.co/1200x600/141419/00f0ff.png?text=Noticia+Gaming
    
    Formato: {{"nuevas_noticias": [ {{"categoria": "...", "titulo": "...", "resumen": "...", "contenido_completo": "<p>...</p>", "imagen": "AQUI LA URL", "enlace": "..."}} ] }}
    Noticias a procesar:\n{textos}"""
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        noticias_ia = json.loads(response.text).get("nuevas_noticias", [])
        for i, n in enumerate(noticias_ia):
            n['fecha'] = datetime.now().isoformat()
            n['id'] = f"not_{int(time.time())}_{i}"
        noticias_totales = noticias_ia + noticias_validas
    except Exception as e: print("Error en noticias:", e)

if noticias_totales:
    with open('noticias.json', 'w', encoding='utf-8') as f:
        json.dump({"destacada": noticias_totales[0], "secundarias": noticias_totales[1:]}, f, ensure_ascii=False, indent=2)


# ==========================================
# FUNCIÓN AUXILIAR: BUSCADOR DE IMÁGENES REALES (RAWG)
# ==========================================
def buscar_portada_juego(titulo_juego):
    if not rawg_key:
        print("Advertencia: No se encontró RAWG_API_KEY. Usando imagen por defecto.")
        return ""
    
    try:
        url = f"https://api.rawg.io/api/games?key={rawg_key}&search={titulo_juego}&page_size=1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                return data["results"][0].get("background_image", "")
    except Exception as e:
        print(f"Error al buscar imagen para {titulo_juego}:", e)
    return ""


# ==========================================
# TAREA 2: SISTEMA DE LANZAMIENTOS CON BÚSQUEDA WEB EN VIVO (CONFIABLE)
# ==========================================
hoy = datetime.now()
meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def calcular_mes_exacto(offset):
    mes_calculado = hoy.month + offset
    anio_calculado = hoy.year
    while mes_calculado < 1:
        mes_calculado += 12
        anio_calculado -= 1
    while mes_calculado > 12:
        mes_calculado -= 12
        anio_calculado += 1
    return f"{meses_nombres[mes_calculado - 1]} {anio_calculado}"

mes_pasado_str = calcular_mes_exacto(-1)
mes_actual_str = f"{meses_nombres[hoy.month - 1]} {hoy.year}"
mes_siguiente_str = calcular_mes_exacto(1)

print(f"Buscando en internet lanzamientos reales para: {mes_pasado_str}, {mes_actual_str} y {mes_siguiente_str}...")

# Definición del esquema JSON estricto
esquema_lanzamientos = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "meses_disponibles": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
        "catalogo": types.Schema(
            type=types.Type.OBJECT,
            properties={
                mes_pasado_str: types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "titulo": types.Schema(type=types.Type.STRING),
                            "fecha": types.Schema(type=types.Type.STRING),
                            "plataformas": types.Schema(type=types.Type.STRING),
                            "descripcion": types.Schema(type=types.Type.STRING)
                        },
                        required=["titulo", "fecha", "plataformas", "descripcion"]
                    )
                ),
                mes_actual_str: types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "titulo": types.Schema(type=types.Type.STRING),
                            "fecha": types.Schema(type=types.Type.STRING),
                            "plataformas": types.Schema(type=types.Type.STRING),
                            "descripcion": types.Schema(type=types.Type.STRING)
                        },
                        required=["titulo", "fecha", "plataformas", "descripcion"]
                    )
                ),
                mes_siguiente_str: types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "titulo": types.Schema(type=types.Type.STRING),
                            "fecha": types.Schema(type=types.Type.STRING),
                            "plataformas": types.Schema(type=types.Type.STRING),
                            "descripcion": types.Schema(type=types.Type.STRING)
                        },
                        required=["titulo", "fecha", "plataformas", "descripcion"]
                    )
                )
            },
            required=[mes_pasado_str, mes_actual_str, mes_siguiente_str]
        )
    },
    required=["meses_disponibles", "catalogo"]
)

# Instrucciones estrictas de verificación periodística
prompt_lanzamientos = f"""
Usa la herramienta de búsqueda integrada de Google para consultar sitios web especializados y de alta reputación en la industria de los videojuegos (como IGN, GameSpot, Vandal, 3DJuegos o Eurogamer) para obtener los calendarios de lanzamientos reales de los siguientes meses: '{mes_pasado_str}', '{mes_actual_str}' y '{mes_siguiente_str}'.

REGLAS CRÍTICAS DE VERACIDAD:
1. SOLO incluye videojuegos cuya fecha exacta de lanzamiento esté 100% CONFIRMADA oficialmente por sus desarrolladores para esos meses específicos.
2. Queda ESTRICTAMENTE PROHIBIDO inventar nombres de juegos, especular o incluir títulos que tengan fechas estimadas como "Q3 2026", "Finales de año" o "Por confirmar". Si la fecha no es un día exacto confirmado, descarta el juego.
3. Intenta recopilar de forma exhaustiva todos los juegos que cumplan los filtros anteriores (tanto grandes producciones como indies populares).
4. Traduce los nombres de las plataformas y descripciones de forma fidedigna al español.
"""

try:
    # Ejecutamos la petición activando el Google Search Grounding
    resp_lanzamientos = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_lanzamientos,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=esquema_lanzamientos,
            # ESTA LÍNEA ACTIVA LA BÚSQUEDA WEB REAL PARA EVITAR ALUCINACIONES:
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )
    
    estructura_json = json.loads(resp_lanzamientos.text)
    
    for mes in estructura_json["meses_disponibles"]:
        if mes in estructura_json["catalogo"]:
            print(f">> Encontrados {len(estructura_json['catalogo'][mes])} juegos verificados para {mes}.")
            for juego in estructura_json["catalogo"][mes]:
                titulo = juego["titulo"]
                print(f"Buscando arte oficial para: {titulo}...")
                
                url_imagen_real = buscar_portada_juego(titulo)
                juego["imagen"] = url_imagen_real
                time.sleep(0.25)
                
    with open('lanzamientos.json', 'w', encoding='utf-8') as f:
        json.dump(estructura_json, f, ensure_ascii=False, indent=2)
        
    print("¡Éxito! lanzamientos.json verificado con Google Search y guardado correctamente.")

except Exception as e:
    print("Error al generar los lanzamientos:", e)
