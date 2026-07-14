import os
import sys
import json
import time
import re
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: TELEMETRÍA AVANZADA (SISTEMA MULTI-MODELO) ===")

api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")
juegos_input = os.environ.get("INPUT_JUEGOS", "").strip()
sobrescribir = os.environ.get("SOBRESCRIBIR", "false").lower() == "true"

if not api_key:
    sys.exit("❌ ERROR: No se encontró GEMINI_API_KEY.")

client = genai.Client(api_key=api_key)
archivo_oficial = "telemetria.json"

def extraer_json_seguro(texto):
    texto = texto.strip()
    match = re.search(r'\{.*\}', texto, re.DOTALL)
    return match.group(0) if match else texto

# --- SISTEMA DE CONTINGENCIA MULTI-MODELO ---
def generar_con_reintentos(prompt_texto, config_ia, max_intentos=3):
    modelos_disponibles = ['gemini-3.5-flash', 'gemini-2.5-flash']
    
    for intento in range(max_intentos):
        for modelo in modelos_disponibles:
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt_texto,
                    config=config_ia
                )
                return response
            except Exception as e:
                error_str = str(e).lower()
                if "503" in error_str or "unavailable" in error_str or "429" in error_str or "quota" in error_str:
                    print(f"⚠️ Modelo {modelo} saturado. Cambiando al siguiente...")
                    continue
                else:
                    raise e 
        
        espera = 10
        print(f"⚠️ Todos los nodos ocupados. Reintentando en {espera} segundos... (Intento {intento+1}/{max_intentos})")
        time.sleep(espera)
        
    raise Exception("❌ Los servidores de IA están inactivos.")

estructura_final = {"juegos": []}
nombres_existentes = []
if os.path.exists(archivo_oficial) and not sobrescribir:
    with open(archivo_oficial, "r", encoding="utf-8") as f:
        try: 
            estructura_final = json.load(f)
            nombres_existentes = [j["titulo"].lower() for j in estructura_final.get("juegos", [])]
        except: pass

juegos_a_procesar = []

if juegos_input:
    print("🛠️ MODO MANUAL DETECTADO.")
    juegos_a_procesar = [j.strip() for j in juegos_input.split(";") if j.strip()]
else:
    print("🌍 MODO AUTOMÁTICO: Buscando exigencia de hardware en PC...")
    prompt_tendencias = f"""
    Eres analista de hardware. Busca los 3 juegos de PC más populares o exigentes de esta semana.
    EXCLUYE ESTOS: {nombres_existentes}.
    Devuelve ÚNICAMENTE un JSON estricto:
    {{ "juegos": ["Juego 1", "Juego 2", "Juego 3"] }}
    """
    try:
        config_tendencias = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.7, tools=[{"google_search": {}}])
        res_tendencias = generar_con_reintentos(prompt_tendencias, config_tendencias)
        data_tendencias = json.loads(extraer_json_seguro(res_tendencias.text))
        juegos_a_procesar = data_tendencias.get("juegos", [])
        print(f"📡 Telemetría detectada para: {juegos_a_procesar}")
    except Exception as e:
        sys.exit(f"❌ Error al buscar tendencias: {e}")

if not juegos_a_procesar:
    sys.exit("❌ No hay juegos para procesar.")

def buscar_portada(titulo):
    if not rawg_key: return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    try:
        url = f"https://api.rawg.io/api/games?key={rawg_key}&search={requests.utils.quote(titulo)}&page_size=1"
        r = requests.get(url, timeout=5).json()
        if r.get("results"):
            return r["results"][0].get("background_image") or "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    except: pass
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"

for titulo in juegos_a_procesar:
    id_juego = re.sub(r'[^a-z0-9]+', '-', titulo.lower()).strip('-')
    
    if any(j["id"] == id_juego for j in estructura_final.get("juegos", [])) and not sobrescribir:
        print(f"⏭️ Saltando '{titulo}': Ya documentado.")
        continue

    print(f"\n⚙️ Analizando telemetría para: {titulo}...")
    imagen_real = buscar_portada(titulo)
    
    prompt = f"""
    Analiza el rendimiento técnico de "{titulo}" en PC. 
    Devuelve ÚNICAMENTE un JSON estricto con la siguiente estructura:
    {{
        "plataformas": "PC, PS5...",
        "calificacion": "8.5",
        "motor_grafico": "Unreal Engine 5",
        "tecnologias": "DLSS, FSR",
        "sinopsis": "Sinopsis corta...",
        "analisis_detallado": "HTML con <p> y <strong> analizando el rendimiento in-game...",
        "requisitos_minimos": ["CPU...", "RAM...", "GPU...", "Almacenamiento..."],
        "requisitos_recomendados": ["CPU...", "RAM...", "GPU...", "Almacenamiento..."]
    }}
    """
    
    try:
        config_tel = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.4, tools=[{"google_search": {}}])
        res = generar_con_reintentos(prompt, config_tel)
        data = json.loads(extraer_json_seguro(res.text))
        
        nuevo_juego = {
            "id": id_juego,
            "titulo": titulo,
            "fecha": time.strftime("%d %b, %Y"),
            "plataformas": data.get("plataformas", "PC"),
            "calificacion": data.get("calificacion", "8.0"),
            "motor_grafico": data.get("motor_grafico", "Custom Engine"),
            "tecnologias": data.get("tecnologias", "Estándar"),
            "sinopsis": data.get("sinopsis", "Análisis de rendimiento in-game."),
            "analisis_detallado": data.get("analisis_detallado", "<p>Datos en proceso...</p>"),
            "requisitos": {
                "minimos": data.get("requisitos_minimos", ["Intel i5", "8GB RAM", "GTX 1060"]),
                "recomendados": data.get("requisitos_recomendados", ["Intel i7", "16GB RAM", "RTX 3060"])
            },
            "imagen": imagen_real
        }
        
        estructura_final["juegos"].append(nuevo_juego)
        with open(archivo_oficial, "w", encoding="utf-8") as f:
            json.dump(estructura_final, f, ensure_ascii=False, indent=2)
            
        time.sleep(5)
            
    except Exception as e:
        print(f"❌ Error procesando {titulo}: {e}")

print("\n✅ Sincronización de telemetría finalizada.")
