import os
import sys
import json
import time
import requests
import urllib.parse
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: TELEMETRÍA (EDICIÓN Y FUSIÓN INTELIGENTE) ===")

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

# 1. CAPTURA DE DATOS DESDE LOS DIFERENTES CUADROS
juegos_raw = os.environ.get("INPUT_JUEGOS", "")
calificacion_cuadro = os.environ.get("INPUT_CALIFICACION", "").strip()
plataformas_cuadro = os.environ.get("INPUT_PLATAFORMAS", "").strip()
requisitos_cuadro = os.environ.get("INPUT_REQUISITOS", "").strip()
analisis_cuadro = os.environ.get("INPUT_ANALISIS", "").strip()
sobrescribir = os.environ.get("SOBRESCRIBIR", "false").lower() == "true"

# Procesamos la lista de títulos usando punto y coma (;)
texto_unificado = juegos_raw.replace("\n", ";")
titulos = [t.strip() for t in texto_unificado.split(';') if t.strip()]

if not titulos:
    print("⚠️ No se detectó ningún título en la casilla principal.")
    sys.exit(0)

# 2. CARGAR EL ARCHIVO BASE ACTUAL
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

# 3. PROCESAR CADA JUEGO EN LA LISTA
for indice, titulo in enumerate(titulos):
    id_juego = titulo.lower().replace(":", "").replace(" ", "-").replace("'", "").replace(".", "")
    
    # Verificamos si el juego YA existe en nuestra base de datos para activar la fusión inteligente
    idx_existente = next((i for i, j in enumerate(estructura_final["juegos"]) if j["id"] == id_juego), None)
    juego_existente = estructura_final["juegos"][idx_existente] if idx_existente is not None else None

    print(f"\n⚙️ Procesando: {titulo}...")
    if juego_existente:
        print("   [i] El juego ya existe en telemetria.json. Modo de Fusión/Edición activado.")

    imagen_real = juego_existente["imagen"] if juego_existente else buscar_portada(titulo)
    
    # Comprobamos si tiene datos manuales en los cuadros (y es el primer juego de la lista enviada)
    es_primer_juego = (indice == 0)
    tiene_datos_manuales = (analisis_cuadro or requisitos_cuadro or calificacion_cuadro or plataformas_cuadro)
    
    if es_primer_juego and tiene_datos_manuales:
        # 🛠️ MODO EDICIÓN / REESCRITURA MANUAL
        print("   [+] Procesando cuadros de texto del formulario...")
        
        # Preparamos las instrucciones para la IA considerando si el juego existe o es totalmente nuevo
        if juego_existente:
            instruccion_contexto = f"""
            Este juego ya tiene un registro previo en nuestra base de datos. 
            Análisis detallado anterior: "{juego_existente.get('analisis_detallado', '')}"
            Requisitos anteriores: {json.dumps(juego_existente.get('requisitos', {}))}
            
            Tu objetivo es actualizar ese registro. Si el usuario te dio un nuevo 'Texto de análisis/sinopsis base', utilízalo y reescríbelo con un estilo 100% original anti-copyright. Si la casilla de análisis base viene vacía o es muy corta, mantén, pule y mejora el análisis detallado anterior.
            """
        else:
            instruccion_contexto = "Este juego es completamente nuevo. Estructura y redacta desde cero basándote en los datos aportados de forma original y técnica."

        prompt = f"""
        Actúas como un redactor técnico senior de videojuegos (estilo Digital Foundry). 
        Analizas el juego: '{titulo}'
        
        {instruccion_contexto}

        Datos nuevos aportados en el formulario por el administrador:
        - Calificación sugerida: "{calificacion_cuadro}"
        - Plataformas sugeridas: "{plataformas_cuadro}"
        - Requisitos crudos: "{requisitos_cuadro}"
        - Texto de análisis/sinopsis base nuevo: "{analisis_cuadro}"

        Instrucciones estrictas:
        1. Si el campo de Requisitos crudos no está vacío, desglósalo en listas para "minimos" y "recomendados". Si está vacío, mantén los del registro anterior si existían, o búscalos tú de forma lógica.
        2. El "analisis_detallado" debe constar de 2 párrafos redactados en HTML (<p>...</p>). Si hay un texto base nuevo, redáctalo para que sea original y libre de copyright.

        Devuelve UNICAMENTE un JSON válido con esta estructura:
        {{
            "fecha": "Fecha de lanzamiento real o estimada",
            "plataformas": "Plataformas (prioriza la nueva sugerida si existe)",
            "calificacion": "Usa la nueva calificación sugerida si existe",
            "motor_grafico": "Motor gráfico utilizado (o conserva el anterior)",
            "tecnologias": "Tecnologías clave deducidas (DLSS, FSR, Ray Tracing, etc.)",
            "rendimiento": "Resolución y FPS objetivo recomendados",
            "sinopsis": "Sinopsis de 2 líneas escrita con tus propias palabras.",
            "analisis_detallado": "<p>Primer párrafo.</p><p>Segundo párrafo técnico.</p>",
            "requisitos": {{
                "minimos": ["Dato 1", "Dato 2"],
                "recomendados": ["Dato 1", "Dato 2"]
            }}
        }}
        """
    else:
        # MODO AUTOMÁTICO TRADICIONAL
        if juego_existente:
            # Si se pasa en modo automático pero ya existe, no gastamos cuota de IA, simplemente lo dejamos pasar idéntico
            print("   [✅] El juego ya está completo y no se enviaron datos nuevos para modificar. Saltando...")
            continue
            
        print("   [+] Investigando en internet (Wikipedia + RAWG)...")
        contexto_web = buscar_info_extra(titulo)
        
        prompt = f"""
        Actúa como experto en hardware y rendimiento. Analiza el juego '{titulo}'.
        Contexto enciclopédico extraído: "{contexto_web}"
        
        Devuelve UNICAMENTE un JSON válido con esta estructura:
        {{
            "fecha": "Fecha de lanzamiento exacta",
            "plataformas": "Plataformas de salida",
            "calificacion": "Nota numérica del 1 al 10 en base a críticas",
            "motor_grafico": "Motor (Ej. Unreal Engine 5)",
            "tecnologias": "Tecnologías (DLSS, Ray Tracing, etc)",
            "rendimiento": "Resolución y FPS objetivo recomendados",
            "sinopsis": "Sinopsis enciclopédica breve",
            "analisis_detallado": "<p>Escribe 2 párrafos técnicos en HTML analizando los gráficos, físicas y rendimiento.</p>",
            "requisitos": {{
                "minimos": ["..."],
                "recomendados": ["..."]
            }}
        }}
        """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(safety_settings=seguridad_permisiva, response_mime_type="application/json")
        )
        data = json.loads(response.text)
        
        # FUSIÓN DE COMPLEMENTARIEDAD: Si el campo del formulario vino vacío, heredamos lo que ya tenía el JSON viejo
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
            print(f"   ✨ Fusión exitosa. Datos antiguos preservados y campos nuevos guardados.")
        else:
            estructura_final["juegos"].append(nuevo_juego)
            print(f"   ✅ Nuevo expediente '{titulo}' guardado.")
        
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
                "sinopsis": "Fallo en la sincronización.",
                "analisis_detallado": f"<p class='text-red-400'>Error en transformación: {error_msg}</p>",
                "requisitos": {"minimos": ["N/A"], "recomendados": ["N/A"]},
                "imagen": imagen_real
            }
            estructura_final["juegos"].append(error_juego)
        
    time.sleep(12)

# 4. APLICAR CAMBIOS EN EL DISCO
with open(archivo_json, 'w', encoding='utf-8') as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print("✅ Base de datos telemetria.json actualizada de forma segura.")
