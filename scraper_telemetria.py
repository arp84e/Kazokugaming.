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

        # =====================================================================
# INYECTAR ESTA LÓGICA EN scraper_telemetria.py AL FINAL DEL BUCLE 'try'
# DE PROCESAMIENTO DE JUEGOS (JUSTO ANTES DEL SECTOR 'except Exception as e')
# =====================================================================
        if idx_existente is not None:
            estructura_final["juegos"][idx_existente] = nuevo_juego
            print(f"   ✨ Fusión exitosa.")
        else:
            estructura_final["juegos"].append(nuevo_juego)
            print(f"   ✅ Expediente guardado.")

        # 🌎 [NUEVO] GENERACIÓN DEL ARCHIVO HTML DE TELEMETRÍA INDIVIDUAL PARA SEO
        os.makedirs("telemetria", exist_ok=True)
        html_juego_filename = f"telemetria/{id_juego}.html"

        req_min = nuevo_juego["requisitos"].get("minimos", [])
        req_rec = nuevo_juego["requisitos"].get("recomendados", [])
        
        html_minimos = "".join([f'<li class="flex items-start space-x-2"><span class="text-cyan-500 mt-0.5 text-xs">▸</span><span>{r}</span></li>' for r in req_min])
        html_recomendados = "".join([f'<li class="flex items-start space-x-2"><span class="text-cyan-500 mt-0.5 text-xs">▸</span><span>{r}</span></li>' for r in req_rec])

        plantilla_juego_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{nuevo_juego["titulo"]} | Análisis Técnico & Telemetría</title>
    <meta name="description" content="{nuevo_juego["sinopsis"]}">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <style> body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0b0f19; }} </style>
</head>
<body class="text-slate-200 min-h-screen flex flex-col justify-between">
    <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex-grow w-full">
        <div class="lg:flex lg:space-x-10 mb-12">
            <div class="lg:w-1/3 mb-8 lg:mb-0">
                <div class="rounded-2xl overflow-hidden shadow-2xl border border-slate-800/80 sticky top-24 relative">
                    <img src="{nuevo_juego["imagen"]}" alt="{nuevo_juego["titulo"]}" class="w-full h-auto object-cover aspect-[3/4]">
                    <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent"></div>
                </div>
            </div>
            <div class="lg:w-2/3 flex flex-col justify-center">
                <div class="flex items-center space-x-3 mb-4">
                    <span class="px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 uppercase tracking-wider">{nuevo_juego["fecha"]}</span>
                </div>
                <div class="flex items-start justify-between mb-2">
                    <h1 class="text-4xl sm:text-5xl font-extrabold text-white tracking-tight pr-4">{nuevo_juego["titulo"]}</h1>
                    <div class="relative flex flex-col items-center justify-center w-20 h-20 min-w-[5rem] bg-slate-900 border-2 border-cyan-500/80 rounded-xl shadow-[0_0_20px_rgba(6,182,212,0.3)]">
                        <span class="text-2xl font-black text-white mt-2">{nuevo_juego["calificacion"]}</span>
                    </div>
                </div>
                <p class="text-sm font-bold text-slate-400 tracking-wide uppercase mb-6">{nuevo_juego["plataformas"]}</p>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
                    <div class="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                        <p class="text-[10px] text-slate-500 uppercase font-bold mb-1">Motor Gráfico</p>
                        <p class="text-sm font-semibold text-cyan-400">{nuevo_juego["motor_grafico"]}</p>
                    </div>
                </div>
                <div class="bg-slate-900/30 border border-slate-800/50 rounded-2xl p-6 text-slate-300">
                    {nuevo_juego["analisis_detallado"]}
                </div>
            </div>
        </div>
        <div class="grid md:grid-cols-2 gap-8 mt-8">
            <div class="bg-slate-950/50 rounded-2xl p-6 border border-slate-800/50">
                <h3 class="text-lg font-bold text-slate-200 mb-4">Mínimos</h3>
                <ul class="space-y-4 text-sm text-slate-400">{html_minimos}</ul>
            </div>
            <div class="bg-cyan-950/10 rounded-2xl p-6 border border-cyan-900/30">
                <h3 class="text-lg font-bold text-cyan-100 mb-4">Recomendados</h3>
                <ul class="space-y-4 text-sm text-slate-300">{html_recomendados}</ul>
            </div>
        </div>
    </main>
    <script src="../header.js"></script>
</body>
</html>"""

        with open(html_juego_filename, "w", encoding="utf-8") as jf:
            jf.write(plantilla_juego_html)
        print(f"🌎 HTML Estático de Telemetría creado en: {html_juego_filename}")
                
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
