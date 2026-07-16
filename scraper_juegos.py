import os
import sys
import json
import time
import re
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: SISTEMA DE JUEGOS Y TOP 10 (MODO MULTI-COMANDO) ===")

api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")
comando_input = os.environ.get("INPUT_COMANDOS", "").strip().lower()
sobrescribir = os.environ.get("SOBRESCRIBIR", "false").lower() == "true"

if not comando_input: comando_input = "top"
if not api_key: sys.exit("❌ ERROR: No se encontró GEMINI_API_KEY.")

client = genai.Client(api_key=api_key)
archivo_oficial = "juegos.json" 

def extraer_json_seguro(texto):
    texto = texto.strip()
    match = re.search(r'\{.*\}', texto, re.DOTALL)
    return match.group(0) if match else texto

def generar_con_reintentos(prompt_texto, config_ia, max_intentos=3):
    modelos_disponibles = ['gemini-3.5-flash', 'gemini-2.5-flash']
    for intento in range(max_intentos):
        for modelo in modelos_disponibles:
            try: return client.models.generate_content(model=modelo, contents=prompt_texto, config=config_ia)
            except Exception as e:
                if "503" in str(e) or "unavailable" in str(e) or "429" in str(e):
                    print(f"⚠️ Modelo {modelo} saturado. Cambiando...")
                    continue
                else: raise e 
        time.sleep(10)
    raise Exception("❌ Servidores inactivos.")

# Cargar base actual
estructura_final = {"juegos": []}
nombres_existentes = []
if os.path.exists(archivo_oficial):
    with open(archivo_oficial, "r", encoding="utf-8") as f:
        try: 
            estructura_final = json.load(f)
            nombres_existentes = [j["titulo"].lower() for j in estructura_final.get("juegos", [])]
        except: pass

juegos_a_procesar = []
top_10_oficial = []
es_modo_top = False

# ================= LÓGICA DE COMANDOS =================
if comando_input == "top":
    print("🌍 COMANDO 'TOP': Escaneando múltiples fuentes para crear el Top 10 Global...")
    es_modo_top = True
    prompt_busqueda = """
    Eres analista de la industria del gaming. Busca en internet en 5 fuentes distintas el Top 10 de los videojuegos más populares o jugados a nivel mundial AHORA.
    Mezcla títulos de PC, Consolas y Móviles.
    Devuelve ÚNICAMENTE un JSON estricto:
    { "resultados": ["Juego 1", "Juego 2", "Juego 3", "Juego 4", "Juego 5", "Juego 6", "Juego 7", "Juego 8", "Juego 9", "Juego 10"] }
    """
elif comando_input.isdigit():
    cantidad = int(comando_input)
    print(f"🎲 COMANDO NUMÉRICO: Buscando {cantidad} juegos populares que NO tengamos...")
    prompt_busqueda = f"""
    Eres analista de gaming. Busca en internet {cantidad} videojuegos populares o en tendencia actualmente (mezcla de PC, Consolas y Móviles).
    EXCLUYE OBLIGATORIAMENTE todos estos títulos que ya están en la base de datos: {nombres_existentes}.
    Devuelve ÚNICAMENTE un JSON estricto:
    {{ "resultados": ["Nombre 1", "Nombre 2"... hasta llegar a {cantidad}] }}
    """
else:
    print(f"🛠️ COMANDO LISTA: Procesando títulos específicos solicitados...")
    juegos_a_procesar = [j.strip() for j in os.environ.get("INPUT_COMANDOS", "").split(";") if j.strip()]

# Si el comando era 'top' o un número, usamos la IA para generar la lista
if comando_input == "top" or comando_input.isdigit():
    try:
        config_busqueda = types.GenerateContentConfig(temperature=0.6, tools=[{"google_search": {}}])
        res_busqueda = generar_con_reintentos(prompt_busqueda, config_busqueda)
        data_busqueda = json.loads(extraer_json_seguro(res_busqueda.text))
        juegos_a_procesar = data_busqueda.get("resultados", [])
        print(f"📡 Nombres obtenidos: {juegos_a_procesar}")
        if es_modo_top: top_10_oficial = juegos_a_procesar
    except Exception as e:
        sys.exit(f"❌ Error al ejecutar comando de búsqueda: {e}")

def buscar_portada(titulo):
    if not rawg_key: return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    try:
        url = f"https://api.rawg.io/api/games?key={rawg_key}&search={requests.utils.quote(titulo)}&page_size=1"
        r = requests.get(url, timeout=5).json()
        if r.get("results"): return r["results"][0].get("background_image") or "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    except: pass
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"

nuevos_agregados = 0

# Procesar y Analizar Rendimiento
for titulo in juegos_a_procesar:
    id_juego = re.sub(r'[^a-z0-9]+', '-', titulo.lower()).strip('-')
    
    if any(j["id"] == id_juego for j in estructura_final.get("juegos", [])) and not sobrescribir:
        print(f"⏭️ '{titulo}' ya existe en la base de datos. Saltando...")
        continue

    print(f"\n⚙️ Analizando telemetría y rendimiento para: {titulo}...")
    imagen_real = buscar_portada(titulo)
    
    prompt = f"""
    Analiza minuciosamente el rendimiento técnico de "{titulo}". (Puede ser PC, Consola o Móvil).
    Devuelve ÚNICAMENTE un JSON estricto con esta estructura:
    {{
        "plataformas": "Ej: PC, PS5, Android...",
        "calificacion": "Ej: 8.5",
        "motor_grafico": "Ej: Unreal Engine 5",
        "tecnologias": "DLSS, Crossplay...",
        "sinopsis": "Sinopsis corta de 2 lineas...",
        "analisis_detallado": "HTML con <p> y <strong> analizando el rendimiento in-game y optimización...",
        "requisitos_minimos": ["Dato 1", "Dato 2", "Dato 3", "Dato 4"],
        "requisitos_recomendados": ["Dato 1", "Dato 2", "Dato 3", "Dato 4"]
    }}
    """
    
    try:
        config_tel = types.GenerateContentConfig(temperature=0.35, tools=[{"google_search": {}}])
        res = generar_con_reintentos(prompt, config_tel)
        data = json.loads(extraer_json_seguro(res.text))
        
        nuevo_juego = {
            "id": id_juego,
            "titulo": titulo,
            "fecha": time.strftime("%d %b, %Y"),
            "plataformas": data.get("plataformas", "Varias"),
            "calificacion": data.get("calificacion", "8.0"),
            "motor_grafico": data.get("motor_grafico", "Custom"),
            "tecnologias": data.get("tecnologias", "Estándar"),
            "sinopsis": data.get("sinopsis", "Análisis en curso."),
            "analisis_detallado": data.get("analisis_detallado", "<p>Datos procesados con IA.</p>"),
            "requisitos": {
                "minimos": data.get("requisitos_minimos", []),
                "recomendados": data.get("requisitos_recomendados", [])
            },
            "imagen": imagen_real
        }
        
        estructura_final["juegos"].append(nuevo_juego)
        nuevos_agregados += 1
        time.sleep(5)
            
    except Exception as e:
        print(f"❌ Error procesando {titulo}: {e}")

# Reorganización SOLO si se utilizó el comando TOP
if es_modo_top:
    print("\n🔄 Reorganizando la base de datos para priorizar el Top 10 al inicio...")
    juegos_top = []
    juegos_resto = []
    top_10_lower = [t.lower() for t in top_10_oficial]

    for j in estructura_final["juegos"]:
        if j["titulo"].lower() in top_10_lower: juegos_top.append(j)
        else: juegos_resto.append(j)

    juegos_top.sort(key=lambda x: top_10_lower.index(x["titulo"].lower()) if x["titulo"].lower() in top_10_lower else 999)
    estructura_final["juegos"] = juegos_top + juegos_resto

with open(archivo_oficial, "w", encoding="utf-8") as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print(f"\n✅ Base de datos 'juegos.json' actualizada ({nuevos_agregados} juegos nuevos agregados).")
