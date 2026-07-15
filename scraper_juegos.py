import os
import sys
import json
import time
import re
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: SISTEMA DE JUEGOS Y TOP 10 GLOBAL (PC, CONSOLAS, MÓVILES) ===")

api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")
juegos_input = os.environ.get("INPUT_JUEGOS", "").strip()
sobrescribir = os.environ.get("SOBRESCRIBIR", "false").lower() == "true"

if not api_key:
    sys.exit("❌ ERROR: No se encontró GEMINI_API_KEY.")

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
            try:
                return client.models.generate_content(model=modelo, contents=prompt_texto, config=config_ia)
            except Exception as e:
                error_str = str(e).lower()
                if "503" in error_str or "unavailable" in error_str or "429" in error_str:
                    print(f"⚠️ Modelo {modelo} saturado. Cambiando...")
                    continue
                else: raise e 
        espera = 10
        print(f"⚠️ Nodos ocupados. Reintentando en {espera}s... ({intento+1}/{max_intentos})")
        time.sleep(espera)
    raise Exception("❌ Servidores inactivos.")

# Cargar base actual
estructura_final = {"juegos": []}
if os.path.exists(archivo_oficial):
    with open(archivo_oficial, "r", encoding="utf-8") as f:
        try: estructura_final = json.load(f)
        except: pass

juegos_a_procesar = []
top_10_oficial = []

if juegos_input:
    print("🛠️ MODO MANUAL: Procesando lista delimitada...")
    juegos_a_procesar = [j.strip() for j in juegos_input.split(";") if j.strip()]
    top_10_oficial = juegos_a_procesar 
else:
    print("🌍 MODO AUTOMÁTICO: Escaneando múltiples fuentes para crear el Top 10 Global...")
    prompt_top10 = """
    Eres un analista experto en la industria del gaming. Busca en internet consultando al menos 5 fuentes distintas el Top 10 de los videojuegos más populares o jugados a nivel mundial en este momento.
    El top debe ser global e incluir una mezcla de títulos de PC, Consolas y Móviles.
    Devuelve ÚNICAMENTE un JSON con esta estructura exacta (sin texto antes ni después):
    { "top_10": ["Nombre del Juego 1", "Nombre del Juego 2", "Nombre del Juego 3", "Nombre del Juego 4", "Nombre del Juego 5", "Nombre del Juego 6", "Nombre del Juego 7", "Nombre del Juego 8", "Nombre del Juego 9", "Nombre del Juego 10"] }
    """
    try:
        # CORRECCIÓN: Se eliminó response_mime_type para evitar el error 400 con google_search
        config_top = types.GenerateContentConfig(temperature=0.5, tools=[{"google_search": {}}])
        res_top = generar_con_reintentos(prompt_top10, config_top)
        data_top = json.loads(extraer_json_seguro(res_top.text))
        top_10_oficial = data_top.get("top_10", [])
        print(f"🏆 TOP 10 Global Consolidado: {top_10_oficial}")
        juegos_a_procesar = top_10_oficial
    except Exception as e:
        sys.exit(f"❌ Error al generar el Top 10: {e}")

def buscar_portada(titulo):
    if not rawg_key: return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    try:
        url = f"https://api.rawg.io/api/games?key={rawg_key}&search={requests.utils.quote(titulo)}&page_size=1"
        r = requests.get(url, timeout=5).json()
        if r.get("results"): return r["results"][0].get("background_image") or "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    except: pass
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"

nuevos_agregados = 0

for titulo in juegos_a_procesar:
    id_juego = re.sub(r'[^a-z0-9]+', '-', titulo.lower()).strip('-')
    
    if any(j["id"] == id_juego for j in estructura_final.get("juegos", [])) and not sobrescribir:
        print(f"⏭️ '{titulo}' ya existe en la base de datos.")
        continue

    print(f"\n⚙️ Analizando datos para: {titulo}...")
    imagen_real = buscar_portada(titulo)
    
    prompt = f"""
    Analiza el rendimiento técnico y detalles de "{titulo}". Puede ser de PC, Consola o Móvil.
    Devuelve ÚNICAMENTE un JSON estricto con la siguiente estructura (sin formato Markdown):
    {{
        "plataformas": "Ej: PC, PS5 / Android, iOS",
        "calificacion": "Ej: 8.5",
        "motor_grafico": "Ej: Unreal Engine, Unity...",
        "tecnologias": "DLSS, Touch, Crossplay...",
        "sinopsis": "Sinopsis corta...",
        "analisis_detallado": "HTML con <p> y <strong> analizando el rendimiento in-game...",
        "requisitos_minimos": ["Dato 1", "Dato 2", "Dato 3", "Dato 4"],
        "requisitos_recomendados": ["Dato 1", "Dato 2", "Dato 3", "Dato 4"]
    }}
    """
    
    try:
        # CORRECCIÓN: Sin response_mime_type
        config_tel = types.GenerateContentConfig(temperature=0.4, tools=[{"google_search": {}}])
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
            "sinopsis": data.get("sinopsis", "Análisis de rendimiento."),
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

print("\n🔄 Reorganizando la base de datos para priorizar el Top 10...")

juegos_top = []
juegos_resto = []
top_10_lower = [t.lower() for t in top_10_oficial]

for j in estructura_final["juegos"]:
    if j["titulo"].lower() in top_10_lower:
        juegos_top.append(j)
    else:
        juegos_resto.append(j)

juegos_top.sort(key=lambda x: top_10_lower.index(x["titulo"].lower()) if x["titulo"].lower() in top_10_lower else 999)

estructura_final["juegos"] = juegos_top + juegos_resto

with open(archivo_oficial, "w", encoding="utf-8") as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print(f"\n✅ Base de datos 'juegos.json' actualizada ({nuevos_agregados} nuevos) y ordenada correctamente.")
