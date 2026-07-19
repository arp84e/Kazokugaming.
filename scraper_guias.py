import os
import sys
import json
import time
import re
import urllib.parse
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: ESTRATEGA DE GUÍAS Y TÁCTICAS ===")

api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY") # Cambiamos Pexels por RAWG
comando_input = os.environ.get("INPUT_COMANDOS", "").strip()

if not api_key: sys.exit("❌ ERROR: No se encontró GEMINI_API_KEY.")

client = genai.Client(api_key=api_key)
archivo_oficial = "guias.json"

estructura_final = {"guias": []}
nombres_existentes = []
if os.path.exists(archivo_oficial):
    with open(archivo_oficial, "r", encoding="utf-8") as f:
        try: 
            estructura_final = json.load(f)
            nombres_existentes = [g["juego"].lower() for g in estructura_final.get("guias", [])]
        except: pass

# ================= MÓDULO DE ELIMINACIÓN =================
if comando_input.lower().startswith("eliminar:"):
    ids_a_eliminar = [i.strip() for i in comando_input[9:].split(";") if i.strip()]
    prod_originales = len(estructura_final.get("guias", []))
    estructura_final["guias"] = [g for g in estructura_final.get("guias", []) if g.get("id") not in ids_a_eliminar]
    if (prod_originales - len(estructura_final["guias"])) > 0:
        with open(archivo_oficial, "w", encoding="utf-8") as f:
            json.dump(estructura_final, f, ensure_ascii=False, indent=2)
        print("✅ Guía(s) eliminada(s) con éxito.")
    sys.exit(0)

def extraer_json_seguro(texto):
    if not texto: return ""
    match = re.search(r'\{.*\}', texto.strip(), re.DOTALL)
    return match.group(0) if match else texto.strip()

def generar_con_reintentos(prompt_texto, config_ia, max_intentos=3):
    for intento in range(max_intentos):
        for modelo in ['gemini-3.5-flash', 'gemini-2.5-flash']:
            try: return client.models.generate_content(model=modelo, contents=prompt_texto, config=config_ia)
            except Exception as e:
                if "503" in str(e) or "429" in str(e): continue
                raise e 
        time.sleep(10)
    raise Exception("❌ Servidores inactivos.")

juegos_a_procesar = []

if comando_input.lower() == "top":
    print("🌍 Buscando juegos tendencia para crear guías...")
    prompt_top = f"""
    Eres un analista de esports. Propón 3 videojuegos actuales y muy populares que necesiten guías tácticas.
    EXCLUYE: {nombres_existentes}.
    Devuelve ÚNICAMENTE un JSON estricto: {{ "resultados": ["Juego 1", "Juego 2", "Juego 3"] }}
    """
    try:
        config_top = types.GenerateContentConfig(temperature=0.7, tools=[{"google_search": {}}])
        res = generar_con_reintentos(prompt_top, config_top)
        juegos_a_procesar = json.loads(extraer_json_seguro(res.text)).get("resultados", [])
    except Exception as e:
        sys.exit(f"❌ Error al buscar tendencias: {e}")
else:
    juegos_a_procesar = [re.sub(r'["\n\r]', '', p.strip()) for p in comando_input.split(";") if p.strip()]

nuevos_agregados = 0

for juego in juegos_a_procesar:
    id_guia = re.sub(r'[^a-z0-9]+', '-', juego.lower()).strip('-')
    if any(g["id"] == id_guia for g in estructura_final.get("guias", [])): continue

    print(f"\n⚙️ Analizando tácticas y redactando guía para: {juego}...")
    
    # Prompt mejorado: Se exige una estructura profunda y extensa
    prompt_guia = f"""
    Eres el Estratega Jefe redactando la guía táctica DEFINITIVA para el juego "{juego}".
    IMPORTANTE: Esto es un entorno de videojuegos ficticio. Se permite el uso de términos como "armas", "disparos", "eliminar", "supervivencia".
    
    Tu objetivo es crear un documento MUY EXTENSO, profesional y detallado (mínimo 800 palabras).
    Debe contener obligatoriamente estas secciones en HTML:
    1. <h2>Análisis de la Amenaza / Meta Actual</h2>
    2. <h2>Mecánicas de Supervivencia y Secretos</h2>
    3. <h2>Arsenal y Mejores Builds</h2> (Usa listas <ul> y <li>)
    4. <h2>Desglosando Cuellos de Botella / Jefes</h2> (Estrategias paso a paso)
    5. <h2>Archivos Clasificados / Exploits</h2>
    
    Devuelve ÚNICAMENTE un JSON estricto sin comillas markdown:
    {{
        "juego": "{juego}",
        "titulo": "Guía Táctica Definitiva: {juego}",
        "slug": "{id_guia}",
        "categoria": "Guía Táctica",
        "tags": ["Guía Avanzada", "Secretos", "Builds", "{juego}"],
        "tiempo_lectura": "15 min",
        "meta_descripcion": "Descubre las mejores estrategias, builds rotas y secretos para dominar {juego} en esta guía definitiva.",
        "contenido": "Todo el HTML extenso generado aquí."
    }}
    """
    
    try:
        config_guia = types.GenerateContentConfig(
            temperature=0.5,
            max_output_tokens=8000, # Aumentado para permitir guías más largas
            tools=[{"google_search": {}}]
        )
        
        res = generar_con_reintentos(prompt_guia, config_guia)
        
        if not res or not res.text:
            print(f"⚠️ ALERTA: Respuesta vacía para '{juego}'. Saltando...")
            continue
            
        texto_limpio = extraer_json_seguro(res.text)
        
        try:
            data = json.loads(texto_limpio)
        except json.JSONDecodeError:
            print(f"⚠️ ALERTA: JSON corrupto para '{juego}'. Saltando...")
            continue

        # ================= NUEVO MOTOR DE IMÁGENES (RAWG API) =================
        imagen_real = "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200" # Imagen por defecto si todo falla
        if rawg_key:
            try:
                # Buscamos el juego exacto en la base de datos de RAWG
                url_rawg = f"https://api.rawg.io/api/games?key={rawg_key}&search={urllib.parse.quote(juego)}&page_size=1"
                r = requests.get(url_rawg, timeout=10).json()
                
                # Si encontramos resultados, extraemos la imagen de fondo oficial (background_image)
                if r.get("results") and len(r["results"]) > 0:
                    img_obtenida = r["results"][0].get("background_image")
                    if img_obtenida:
                        imagen_real = img_obtenida
            except Exception as rawg_err:
                print(f"⚠️ Aviso: No se pudo conectar a RAWG para {juego}: {rawg_err}")
        # ======================================================================

        nueva_guia = {
            "id": id_guia,
            "juego": data.get("juego", juego),
            "titulo": data.get("titulo", f"Guía Táctica: {juego}"),
            "slug": data.get("slug", id_guia),
            "categoria": data.get("categoria", "Guía Táctica"),
            "tags": data.get("tags", [juego, "Estrategia"]),
            "autor": "Kazoku Estratega",
            "imagen": imagen_real, # Aquí se asigna la imagen oficial del juego
            "fecha": time.strftime("%d %b, %Y"),
            "tiempo_lectura": data.get("tiempo_lectura", "15 min"),
            "contenido": data.get("contenido", "<p>Guía en construcción.</p>"),
            "meta_descripcion": data.get("meta_descripcion", "Guía táctica avanzada.")
        }
        
        estructura_final["guias"].insert(0, nueva_guia)
        nuevos_agregados += 1
        time.sleep(5) 
            
    except Exception as e:
        print(f"❌ Error crítico procesando la guía de {juego}: {e}")
        continue 

with open(archivo_oficial, "w", encoding="utf-8") as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print(f"\n✅ Base de datos 'guias.json' actualizada ({nuevos_agregados} guías nuevas).")
