import os
import sys
import json
import time
import requests
import urllib.parse
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: TELEMETRÍA (FUSIÓN INTELIGENTE + ANTI-SATURACIÓN) ===")

# Configuración de APIs
api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")

if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# Configuración de seguridad
seguridad_permisiva = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

def buscar_portada(titulo):
    if not rawg_key: return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"
    try:
        url = f"https://api.rawg.io/api/games?key={rawg_key}&search={titulo}&page_size=1"
        res = requests.get(url).json()
        if res.get('results'):
            return res['results'][0]['background_image']
    except:
        pass
    return "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800"

def buscar_info_extra(titulo):
    try:
        query = urllib.parse.quote(titulo + " videojuego")
        url_search = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&utf8=&format=json"
        res_search = requests.get(url_search).json()
        
        if res_search['query']['search']:
            page_title = res_search['query']['search'][0]['title']
            url_summary = f"https://es.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(page_title)}"
            res_summary = requests.get(url_summary).json()
            return res_summary.get('extract', 'Sin datos en Wikipedia.')
    except:
        pass
    return "Utiliza tu base de datos interna para obtener precisión técnica."

# 1. CAPTURA DE DATOS
juegos_raw = os.environ.get("INPUT_JUEGOS", "")
calificacion_cuadro = os.environ.get("INPUT_CALIFICACION", "").strip()
plataformas_cuadro = os.environ.get("INPUT_PLATAFORMAS", "").strip()
requisitos_cuadro = os.environ.get("INPUT_REQUISITOS", "").strip()
analisis_cuadro = os.environ.get("INPUT_ANALISIS", "").strip()
sobrescribir = os.environ.get("SOBRESCRIBIR", "false").lower() == "true"

texto_unificado = juegos_raw.replace("\n", ";")
titulos = [t.strip() for t in texto_unificado.split(';') if t.strip()]

if not titulos:
    print("⚠️ No se detectó ningún título en la casilla principal.")
    sys.exit(0)

# 2. CARGAR ARCHIVO
estructura_final = {"juegos": []}
archivo_json = 'telemetria.json'

if not sobrescribir and os.path.exists(archivo_json):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos_viejos = json.load(f)
            if isinstance(datos_viejos, dict) and "juegos" in datos_viejos:
                estructura_final["juegos"] = datos_viejos["juegos"]
    except:
        pass

# 3. PROCESAR JUEGOS
for indice, titulo in enumerate(titulos):
    id_juego = titulo.lower().replace(":", "").replace(" ", "-").replace("'", "").replace(".", "")
    
    idx_existente = next((i for i, j in enumerate(estructura_final["juegos"]) if j["id"] == id_juego), None)
    juego_existente = estructura_final["juegos"][idx_existente] if idx_existente is not None else None

    print(f"\n⚙️ Procesando: {titulo}...")
    if juego_existente:
        print("   [i] Juego existente en BD. Modo Fusión activado.")

    imagen_real = juego_existente["imagen"] if juego_existente else buscar_portada(titulo)
    
    es_primer_juego = (indice == 0)
    tiene_datos_manuales = (analisis_cuadro or requisitos_cuadro or calificacion_cuadro or plataformas_cuadro)
    
    if es_primer_juego and tiene_datos_manuales:
        print("   [+] Inyectando datos manuales y reescribiendo...")
        
        if juego_existente:
            instruccion_contexto = f"""
            Este juego ya tiene un registro previo. 
            Análisis anterior: "{juego_existente.get('analisis_detallado', '')}"
            Requisitos anteriores: {json.dumps(juego_existente.get('requisitos', {}))}
            Actualiza el registro. Si hay un texto base nuevo, reescríbelo (anti-copyright). Si no lo hay, mantén el anterior mejorado.
            """
        else:
            instruccion_contexto = "Juego nuevo. Estructura basándote en los datos aportados."

        prompt = f"""
        Actúas como redactor técnico senior. Analizas: '{titulo}'
        {instruccion_contexto}
        Datos nuevos:
        - Calificación: "{calificacion_cuadro}"
        - Plataformas: "{plataformas_cuadro}"
        - Requisitos crudos: "{requisitos_cuadro}"
        - Texto base nuevo: "{analisis_cuadro}"

        Devuelve UNICAMENTE un JSON válido:
        {{
            "fecha": "Fecha estimada",
            "plataformas": "Plataformas",
            "calificacion": "Nota numérica",
            "motor_grafico": "Motor utilizado",
            "tecnologias": "Tecnologías clave (DLSS, etc)",
            "rendimiento": "Resolución y FPS recomendados",
            "sinopsis": "Sinopsis de 2 líneas",
            "analisis_detallado": "<p>Primer párrafo.</p><p>Segundo párrafo técnico.</p>",
            "requisitos": {{
                "minimos": ["..."],
                "recomendados": ["..."]
            }}
        }}
        """
    else:
        if juego_existente:
            print("   [✅] Completo. Sin datos nuevos para modificar. Saltando...")
            continue
            
        print("   [+] Investigando en internet...")
        contexto_web = buscar_info_extra(titulo)
        
        prompt = f"""
        Actúa como experto en hardware y rendimiento. Analiza: '{titulo}'.
        Contexto extraído: "{contexto_web}"
        
        Devuelve UNICAMENTE un JSON válido:
        {{
            "fecha": "Fecha de lanzamiento",
            "plataformas": "Plataformas de salida",
            "calificacion": "Nota numérica del 1 al 10",
            "motor_grafico": "Motor",
            "tecnologias": "Tecnologías",
            "rendimiento": "Resolución y FPS",
            "sinopsis": "Sinopsis breve",
            "analisis_detallado": "<p>Escribe 2 párrafos técnicos en HTML analizando los gráficos y rendimiento.</p>",
            "requisitos": {{
                "minimos": ["..."],
                "recomendados": ["..."]
            }}
        }}
        """
    
    try:
        # 🛡️ NUEVO SISTEMA ANTI-SATURACIÓN (REINTENTOS)
        max_intentos = 3
        intento_actual = 0
        data = None
        
        while intento_actual < max_intentos:
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(safety_settings=seguridad_permisiva, response_mime_type="application/json")
                )
                data = json.loads(response.text)
                break # Si tiene éxito, rompemos el bucle de reintentos
                
            except Exception as e_ia:
                error_str = str(e_ia)
                if "503" in error_str or "429" in error_str:
                    intento_actual += 1
                    espera = 20 * intento_actual
                    print(f"   [⏳] Servidores de IA saturados (Error 503). Esperando {espera} segundos para reintentar ({intento_actual}/{max_intentos})...")
                    time.sleep(espera)
                else:
                    raise e_ia # Si es un error distinto a conexión, lo lanza normalmente
        
        if not data:
            raise Exception("Imposible conectar con la IA después de 3 intentos debido a servidores saturados.")

        # FUSIÓN
        fecha_final = data.get("fecha") if data.get("fecha") else (juego_existente.get("fecha", "Por determinar") if juego_existente else "Por determinar")
        plataformas_final = plataformas_cuadro if plataformas_cuadro else (data.get("plataformas") if data.get("plataformas") else (juego_existente.get("plataformas", "Multiplataforma") if juego_existente else "Multiplataforma"))
        calificacion_final = calificacion_cuadro if calificacion_cuadro else (data.get("calificacion") if data.get("calificacion") else (juego_existente.get("calificacion", "N/A") if juego_existente else "N/A"))
        motor_final = data.get("motor_grafico") if data.get("motor_grafico") and data.get("motor_grafico") != "No especificado" else (juego_existente.get("motor_grafico", "No especificado") if juego_existente else "No especificado")
        tecnologias_final = data.get("tecnologias") if data.get("tecnologias") and data.get("tecnologias") != "Estándar" else (juego_existente.get("tecnologias", "Estándar") if juego_existente else "Estándar")
        rendimiento_final = data.get("rendimiento") if data.get("rendimiento") and data.get("rendimiento") != "Variable" else (juego_existente.get("rendimiento", "Variable") if juego_existente else "Variable")
        sinopsis_final = data.get("sinopsis") if data.get("sinopsis") else (juego_existente.get("sinopsis", "") if juego_existente else "")
        analisis_final = data.get("analisis_detallado") if data.get("analisis_detallado") and "Análisis en proceso" not in data.get("analisis_detallado") else (juego_existente.get("analisis_detallado", "<p>Análisis en proceso...</p>") if juego_existente else "<p>Análisis en proceso...</p>")
        requisitos_final = data.get("requisitos") if data.get("requisitos") and data.get("requisitos", {}).get("minimos") else (juego_existente.get("requisitos", {"minimos": [], "recomendados": []}) if juego_existente else {"minimos": [], "recomendados": []})

        nuevo_juego = {
            "id": id_juego,
            "titulo": juego_existente["titulo"] if juego_existente else titulo,
            "fecha": fecha_final,
            "plataformas": plataformas_final,
            "calificacion": calificacion_final,
            "motor_grafico": motor_final,
            "tecnologias": tecnologias_final,
            "rendimiento": rendimiento_final,
            "sinopsis": sinopsis_final,
            "analisis_detallado": analisis_final,
            "requisitos": requisitos_final,
            "imagen": imagen_real
        }
        
        if idx_existente is not None:
            estructura_final["juegos"][idx_existente] = nuevo_juego
            print(f"   ✨ Fusión exitosa.")
        else:
            estructura_final["juegos"].append(nuevo_juego)
            print(f"   ✅ Expediente guardado.")
        
    except Exception as e:
        print(f"❌ Error procesando {titulo}: {e}")
        if not juego_existente:
            error_msg = str(e).replace('"', "'")
            error_juego = {
                "id": id_juego,
                "titulo": f"⚠️ {titulo}",
                "fecha": "ERROR",
                "plataformas": "N/A",
                "calificacion": calificacion_cuadro if calificacion_cuadro else "0.0",
                "motor_grafico": "N/A",
                "tecnologias": "N/A",
                "rendimiento": "N/A",
                "sinopsis": "Fallo en sincronización.",
                "analisis_detallado": f"<p class='text-red-400'>Error: {error_msg}</p>",
                "requisitos": {"minimos": ["N/A"], "recomendados": ["N/A"]},
                "imagen": imagen_real
            }
            estructura_final["juegos"].append(error_juego)
        
    time.sleep(12)

# 4. GUARDAR
with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print("✅ Base de datos telemetria.json actualizada.")
