import os
import json
import time
import re
import urllib.parse
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: ESTRATEGA DE GUÍAS TÁCTICAS (SISTEMA MULTI-MODELO) ===")

api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")

if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    exit(1)

client = genai.Client(api_key=api_key)
archivo_guias = "guias.json"

# Corrección de lectura JSON para evitar errores si la IA pone texto extra
def extraer_json_seguro(texto):
    texto = texto.strip()
    match = re.search(r'\{.*\}', texto, re.DOTALL)
    if match:
        return match.group(0)
    return texto

# --- SISTEMA DE CONTINGENCIA MULTI-MODELO (FALLBACK) ---
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
                # Si el error es por saturación, intenta con el siguiente modelo al instante
                if "503" in error_str or "unavailable" in error_str or "429" in error_str or "quota" in error_str:
                    print(f"⚠️ Modelo {modelo} saturado. Cambiando al siguiente...")
                    continue
                else:
                    # Si el error es de sintaxis o clave inválida, detenemos
                    raise e
        
        # Si llega aquí, significa que AMBOS modelos están caídos. Hace una pausa corta.
        espera = 10 # Tiempo fijo y corto
        print(f"⚠️ Red neuronal congestionada. Reintentando en {espera} segundos... (Intento {intento+1}/{max_intentos})")
        time.sleep(espera)
        
    raise Exception("❌ Se superó el límite máximo de reintentos. Los servidores de IA están inactivos.")

# Cargar base de datos
datos_web = {"guias": []}
nombres_existentes = []
if os.path.exists(archivo_guias):
    with open(archivo_guias, "r", encoding="utf-8") as f:
        try: 
            datos_web = json.load(f)
            nombres_existentes = [g.get("juego", "").lower() for g in datos_web.get("guias", [])]
        except: pass

entrada_usuario = os.environ.get("INPUT_JUEGO", "").strip()
juegos_a_procesar = []

if entrada_usuario:
    print("🛠️ MODO MANUAL DETECTADO.")
    juegos_a_procesar = [entrada_usuario]
else:
    print("🌍 MODO PILOTO AUTOMÁTICO: Buscando tendencias...")
    prompt_tendencias = f"""
    Eres analista de la industria de los videojuegos.
    Busca en internet cuáles son los 3 videojuegos más buscados o jugados esta semana.
    EXCLUYE estos juegos que ya tenemos: {nombres_existentes}.
    Devuelve ÚNICAMENTE un JSON con esta estructura (añade el año de lanzamiento):
    {{ "juegos": ["Nombre Juego 1 : Año", "Nombre Juego 2 : Año", "Nombre Juego 3 : Año"] }}
    """
    try:
        config_tendencias = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.7, tools=[{"google_search": {}}])
        res_tendencias = generar_con_reintentos(prompt_tendencias, config_tendencias)
        data_tendencias = json.loads(extraer_json_seguro(res_tendencias.text))
        juegos_a_procesar = data_tendencias.get("juegos", [])
        print(f"📡 Tendencias detectadas: {juegos_a_procesar}")
    except Exception as e:
        print(f"❌ Error al buscar tendencias: {e}")
        exit(1)

if not juegos_a_procesar:
    print("❌ No hay juegos para procesar.")
    exit(1)

# Procesamiento principal
for entrada in juegos_a_procesar:
    año_especifico = ""
    juego_limpio = entrada

    if ":" in entrada:
        partes = entrada.split(":")
        juego_limpio = partes[0].strip()
        año_especifico = partes[1].strip()

    slug = re.sub(r'[^a-z0-9]+', '-', juego_limpio.lower()).strip('-')
    id_guia = f"guia-{slug}"[:50]

    if any(g.get("id") == id_guia for g in datos_web.get("guias", [])):
        print(f"⏭️ Saltando '{juego_limpio}': Ya existe en guias.json.")
        continue

    print(f"\n🔍 Redactando dossier para: {juego_limpio} ({año_especifico})...")
    filtro_temporal = f"Lanzado específicamente en el año {año_especifico}." if año_especifico else ""

    prompt_sistema = f"""
    Eres el Estratega Jefe de KazokuGaming. Escribe una GUÍA TÁCTICA AVANZADA.
    Juego: "{juego_limpio}". {filtro_temporal}
    Redacta todo con estilo analítico, oscuro y experto. Usa tags HTML <h2> y <p>.

    ESTRUCTURA JSON OBLIGATORIA (usa comillas simples dentro del HTML):
    {{
      "titulo": "Guía Táctica: [Nombre]",
      "meta_descripcion": "Resumen de 150 caracteres",
      "tags": ["Tag1", "Tag2"],
      "tiempo_lectura": "5 min",
      "contenido": "<h2>Análisis</h2><p>Texto...</p><h2>Mejores Builds</h2><p>Texto...</p>",
      "seo": {{ "keywords": "palabra1, palabra2" }},
      "open_graph": {{ "og_title": "Título", "og_description": "Desc", "og_type": "article" }}
    }}
    """

    try:
        termino_busqueda = f"Guia completa jefes armas secretos {juego_limpio} {año_especifico}".strip()
        config_guia = types.GenerateContentConfig(system_instruction=prompt_sistema, response_mime_type="application/json", temperature=0.35, tools=[{"google_search": {}}])
        
        response = generar_con_reintentos(f"Investiga y redacta la guía de: {termino_busqueda}", config_guia)
        guia_generada = json.loads(extraer_json_seguro(response.text))
        
        imagen_final = "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200"
        if rawg_key:
            try:
                query_rawg = f"{juego_limpio} {año_especifico}".strip()
                r = requests.get(f"https://api.rawg.io/api/games?key={rawg_key}&search={urllib.parse.quote(query_rawg)}&page_size=1", timeout=5).json()
                if r.get("results"): imagen_final = r["results"][0].get("background_image", imagen_final)
            except: pass
        
        guia_final = {
            "id": id_guia,
            "juego": juego_limpio,
            "titulo": guia_generada.get("titulo", f"Guía de {juego_limpio}"),
            "slug": slug,
            "categoria": "Guía Táctica",
            "tags": guia_generada.get("tags", []),
            "autor": "Kazoku Estratega",
            "imagen": imagen_final,
            "fecha": time.strftime("%d %b, %Y"),
            "tiempo_lectura": guia_generada.get("tiempo_lectura", "7 min"),
            "contenido": guia_generada.get("contenido", ""),
            "meta_descripcion": guia_generada.get("meta_descripcion", ""),
            "seo": guia_generada.get("seo", {}),
            "open_graph": guia_generada.get("open_graph", {})
        }
        
        datos_web["guias"].insert(0, guia_final)
        print(f"✅ ¡Dossier de {juego_limpio} guardado con éxito!")
        
        with open(archivo_guias, "w", encoding="utf-8") as f:
            json.dump(datos_web, f, ensure_ascii=False, indent=2)
            
        time.sleep(5) # Tiempo reducido a 5s por seguridad de cuota

    except Exception as e:
        print(f"❌ Error al procesar {juego_limpio}: {e}")

print("\n🚀 PROCESO FINALIZADO.")
