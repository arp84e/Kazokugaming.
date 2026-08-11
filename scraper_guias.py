import os
import sys
import json
import time
import re
import urllib.parse
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: TALLER DE MANTENIMIENTO Y MODDING ===")

api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")
comando_input = os.environ.get("INPUT_COMANDOS", "").strip()

if not api_key:
    sys.exit("❌ ERROR: No se encontró GEMINI_API_KEY.")

client = genai.Client(api_key=api_key)
archivo_oficial = "guias.json"

estructura_final = {"guias": []}
nombres_existentes = []

if os.path.exists(archivo_oficial):
    with open(archivo_oficial, "r", encoding="utf-8") as f:
        try: 
            estructura_final = json.load(f)
            nombres_existentes = [g["juego"].lower() for g in estructura_final.get("guias", [])]
        except Exception:
            pass

# ================= MÓDULO DE ELIMINACIÓN =================
if comando_input.lower().startswith("eliminar:"):
    ids_a_eliminar = [i.strip() for i in comando_input[9:].split(";") if i.strip()]
    prod_originales = len(estructura_final.get("guias", []))
    estructura_final["guias"] = [g for g in estructura_final.get("guias", []) if g.get("id") not in ids_a_eliminar]
    if (prod_originales - len(estructura_final["guias"])) > 0:
        with open(archivo_oficial, "w", encoding="utf-8") as f:
            json.dump(estructura_final, f, ensure_ascii=False, indent=2)
        print("✅ Guía(s) de mantenimiento eliminada(s) con éxito.")
    sys.exit(0)

def extraer_json_seguro(texto):
    if not texto: return ""
    match = re.search(r'\{.*\}', texto.strip(), re.DOTALL)
    return match.group(0) if match else texto.strip()

def generar_con_reintentos(prompt_texto, config_ia, max_intentos=3):
    # Lista de modelos vigentes ordenados por prioridad
    modelos_disponibles = ['gemini-3.5-flash', 'gemini-2.5-flash']
    
    for intento in range(max_intentos):
        for modelo in modelos_disponibles:
            try:
                # Intenta generar el contenido con el modelo actual
                return client.models.generate_content(
                    model=modelo, 
                    contents=prompt_texto, 
                    config=config_ia
                )
            except Exception as e:
                # Si el modelo no existe (404) o está saturado (503/429), pasa al siguiente
                if "404" in str(e) or "503" in str(e) or "429" in str(e):
                    print(f"⚠️ Aviso: El modelo '{modelo}' no respondió ({e}). Probando alternativa...")
                    continue
                raise e 
        time.sleep(5)
    raise Exception("❌ Servidores de IA inactivos o modelos no disponibles.")

temas_a_procesar = []

if comando_input.lower() == "top":
    print("🛠️ Buscando temas populares de mantenimiento y modding...")
    prompt_top = f"""
    Eres un técnico especialista en hardware de videojuegos y PC. Propón 3 tutoriales clave de mantenimiento, modding o reparación de consolas (PS5, Switch, Xbox, PS4, etc.), controles (DualSense, Xbox, Joy-Con drift) o componentes de PC (fuentes, pasta térmica, GPUs).
    EXCLUYE TEMAS YA EXISTENTES: {nombres_existentes}.
    Devuelve ÚNICAMENTE un JSON estricto: {{ "resultados": ["Mantenimiento a X", "Modding Y en Z", "Reparación A de B"] }}
    """
    try:
        config_top = types.GenerateContentConfig(temperature=0.7, tools=[{"google_search": {}}])
        res = generar_con_reintentos(prompt_top, config_top)
        temas_a_procesar = json.loads(extraer_json_seguro(res.text)).get("resultados", [])
    except Exception as e:
        sys.exit(f"❌ Error al buscar tendencias de hardware: {e}")
else:
    temas_a_procesar = [re.sub(r'["\n\r]', '', p.strip()) for p in comando_input.split(";") if p.strip()]

nuevos_agregados = 0

for tema in temas_a_procesar:
    id_guia = re.sub(r'[^a-z0-9]+', '-', tema.lower()).strip('-')
    if any(g["id"] == id_guia for g in estructura_final.get("guias", [])): continue

    print(f"\n⚙️ Generando manual de taller detallado para: {tema}...")
    
    prompt_guia = f"""
    Eres el Técnico Máster en Hardware de KazokuGaming. Tu tarea es rediseñar y escribir una guía de taller EXTREMADAMENTE DETALLADA, paso a paso, limpia y accesible para principiantes sobre: "{tema}".

    Requisitos estrictos de contenido (en formato HTML estructurado):
    1. <h2>🛠️ Herramientas y Materiales Necesarios</h2>
       Usa <ul> y <li> con iconos o nombres de herramientas exactas (ej. destornilladores Torx T8 Security, alcohol isopropílico 99%, limpia contactos, cautín, etc.).
    2. <h2>⚠️ Advertencias de Seguridad y Riesgos</h2>
       Puntos clave de precaución (electricidad estática, condensadores de fuentes, electricidad residual, pérdida de garantía).
    3. <h2>📋 Procedimiento Paso a Paso</h2>
       Proporciona entre 4 y 7 pasos numerados usando <h3>Paso 1: [Nombre]</h3>, <h3>Paso 2: [Nombre]</h3>, etc. Explicaciones súper claras sin dar nada por sentado.
    4. <h2>🔍 Pruebas y Verificación Final</h2>
       Instrucciones sobre cómo reensamblar, probar el equipo y verificar que todo funcione correctamente.
    5. <h2>💡 Solución de Problemas Frecuentes</h2>
       Breve tabla o lista de posibles fallas comunes durante el procedimiento y cómo resolverlas.

    Devuelve ÚNICAMENTE un JSON estricto sin bloques de código ni comillas markdown:
    {{
        "juego": "{tema}",
        "titulo": "Guía de Mantenimiento: {tema}",
        "slug": "{id_guia}",
        "categoria": "Mantenimiento & Modding",
        "tags": ["Hardware", "Mantenimiento", "Modding", "Reparación"],
        "tiempo_lectura": "20 min",
        "meta_descripcion": "Manual paso a paso para realizar mantenimiento, reparación o modding de {tema} de forma segura.",
        "contenido": "Todo el HTML completo y bien estructurado aquí."
    }}
    """
    
    try:
        config_guia = types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=8000,
            tools=[{"google_search": {}}]
        )
        
        res = generar_con_reintentos(prompt_guia, config_guia)
        if not res or not res.text: continue
            
        texto_limpio = extraer_json_seguro(res.text)
        data = json.loads(texto_limpio)

        # Selección de imagen de hardware
        imagen_real = "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?q=80&w=1200" # Foto técnica genérica
        
        # Intentar buscar en RAWG si menciona consolas/juegos o fallback Unsplash de electrónica
        if rawg_key:
            try:
                url_rawg = f"https://api.rawg.io/api/games?key={rawg_key}&search={urllib.parse.quote(tema)}&page_size=1"
                r = requests.get(url_rawg, timeout=8).json()
                if r.get("results") and len(r["results"]) > 0:
                    img_obtenida = r["results"][0].get("background_image")
                    if img_obtenida: imagen_real = img_obtenida
            except Exception:
                pass

        nueva_guia = {
            "id": id_guia,
            "juego": data.get("juego", tema),
            "titulo": data.get("titulo", f"Manual Técnico: {tema}"),
            "slug": data.get("slug", id_guia),
            "categoria": data.get("categoria", "Hardware & Mods"),
            "tags": data.get("tags", ["Hardware", "Taller", "Paso a Paso"]),
            "autor": "Kazoku Técnico Máster",
            "imagen": imagen_real,
            "fecha": time.strftime("%d %b, %Y"),
            "tiempo_lectura": data.get("tiempo_lectura", "20 min"),
            "contenido": data.get("contenido", "<p>Guía en construcción.</p>"),
            "meta_descripcion": data.get("meta_descripcion", "Manual técnico de mantenimiento de hardware.")
        }
        
        estructura_final["guias"].insert(0, nueva_guia)
        nuevos_agregados += 1
        time.sleep(3) 
            
    except Exception as e:
        print(f"❌ Error procesando el tema {tema}: {e}")
        continue 

with open(archivo_oficial, "w", encoding="utf-8") as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print(f"\n✅ Base de datos 'guias.json' actualizada ({nuevos_agregados} manuales nuevos).")
