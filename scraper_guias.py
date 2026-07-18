import os
import sys
import json
import time
import re
import urllib.parse
import random
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: ESTRATEGA DE GUÍAS Y TÁCTICAS ===")

api_key = os.environ.get("GEMINI_API_KEY")
pexels_key = os.environ.get("PEXELS_API_KEY")
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
    
    prompt_guia = f"""
    Eres un jugador profesional de eSports redactando una guía para el juego "{juego}".
    IMPORTANTE: Esto es un entorno de videojuegos ficticio. Se permite el uso de términos como "armas", "disparos", "eliminar", "supervivencia", ya que son mecánicas del juego.
    
    Redacta un dossier táctico muy detallado para dominar el juego.
    
    Devuelve ÚNICAMENTE un JSON estricto sin comillas markdown con las siguientes claves exactas:
    {{
        "juego": "{juego}",
        "titulo": "Guía Táctica Avanzada: Dominando {juego}",
        "slug": "{id_guia}",
        "categoria": "Guía Táctica",
        "tags": ["Tag 1", "Tag 2", "Tag 3", "{juego}"],
        "tiempo_lectura": "5 min",
        "meta_descripcion": "Gancho de 2 líneas con el beneficio principal de leer esta guía.",
        "contenido": "HTML con <h2>, <p>, <ul>. Profundiza en mecánicas avanzadas, mejores armas o estrategias de posicionamiento.",
        "prompt_portada": "Palabras en inglés muy simples para buscar una foto representativa (ej: 'cyberpunk city', 'fantasy landscape')"
    }}
    """
    
    try:
        config_guia = types.GenerateContentConfig(
            temperature=0.5,
            max_output_tokens=4000,
            tools=[{"google_search": {}}]
        )
        
        res = generar_con_reintentos(prompt_guia, config_guia)
        
        if not res or not res.text:
            print(f"⚠️ ALERTA: Gemini devolvió una respuesta vacía para '{juego}'. Posible bloqueo de seguridad por violencia ficticia. Saltando juego...")
            continue
            
        texto_limpio = extraer_json_seguro(res.text)
        
        try:
            data = json.loads(texto_limpio)
        except json.JSONDecodeError:
            print(f"⚠️ ALERTA: El JSON generado para '{juego}' está corrupto. Saltando para no detener la ejecución global...")
            continue

        imagen_real = "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200"
        if pexels_key:
            try:
                prompt_img = data.get('prompt_portada', 'video game')
                r = requests.get(f"https://api.pexels.com/v1/search?query={urllib.parse.quote(prompt_img)}&per_page=1", headers={"Authorization": pexels_key}, timeout=5).json()
                if r.get("photos"): imagen_real = r["photos"][0]["src"]["landscape"]
            except: pass

        nueva_guia = {
            "id": id_guia,
            "juego": data.get("juego", juego),
            "titulo": data.get("titulo", f"Guía Táctica: {juego}"),
            "slug": data.get("slug", id_guia),
            "categoria": data.get("categoria", "Guía Táctica"),
            "tags": data.get("tags", [juego, "Estrategia"]),
            "autor": "Kazoku Estratega",
            "imagen": imagen_real,
            "fecha": time.strftime("%d %b, %Y"),
            "tiempo_lectura": data.get("tiempo_lectura", "5 min"),
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
