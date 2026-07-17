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

print("=== INICIANDO KAZOKUBOT: ANALISTA DE HARDWARE Y TECNOLOGÍA ===")

# --- CONFIGURA AQUÍ TU TAG DE AFILIADO DE AMAZON ---
TAG_AFILIADO = "kazokugaming-21" 

api_key = os.environ.get("GEMINI_API_KEY")
pexels_key = os.environ.get("PEXELS_API_KEY")
input_productos = os.environ.get("INPUT_PRODUCTOS", "").strip()
input_links = os.environ.get("INPUT_LINKS", "").strip()

if not api_key: sys.exit("❌ ERROR: No se encontró GEMINI_API_KEY.")
client = genai.Client(api_key=api_key)
archivo_oficial = "tecnologia.json"

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

estructura_final = {"productos": []}
nombres_existentes = []
if os.path.exists(archivo_oficial):
    with open(archivo_oficial, "r", encoding="utf-8") as f:
        try: 
            estructura_final = json.load(f)
            nombres_existentes = [p["titulo"].lower() for p in estructura_final.get("productos", [])]
        except: pass

productos_a_procesar = []
links_manuales = []

if input_productos:
    print("🛠️ MODO MANUAL: Procesando lista delimitada...")
    # SEGURIDAD: Limpieza de inputs contra Prompt Injection
    productos_a_procesar = [re.sub(r'["\n\r]', '', p.strip()) for p in input_productos.split(";") if p.strip()]
    links_manuales = [re.sub(r'["\n\r]', '', l.strip()) for l in input_links.split(";")] if input_links else []
else:
    print("🌍 MODO AUTOMÁTICO: Escaneando tendencias tecnológicas (Hardware, Gadgets)...")
    prompt_top = f"""
    Eres analista de tecnología. Busca en internet 3 productos tecnológicos (hardware, periféricos, componentes de PC o gadgets) que acaben de salir al mercado o estén en súper tendencia hoy.
    EXCLUYE: {nombres_existentes}.
    Devuelve ÚNICAMENTE un JSON estricto:
    {{ "resultados": ["Producto 1", "Producto 2", "Producto 3"] }}
    """
    try:
        config_top = types.GenerateContentConfig(temperature=0.6, tools=[{"google_search": {}}])
        res_top = generar_con_reintentos(prompt_top, config_top)
        data_top = json.loads(extraer_json_seguro(res_top.text))
        productos_a_procesar = data_top.get("resultados", [])
        print(f"📡 Productos detectados: {productos_a_procesar}")
    except Exception as e:
        sys.exit(f"❌ Error al buscar tendencias: {e}")

nuevos_agregados = 0

for i, prod in enumerate(productos_a_procesar):
    id_prod = re.sub(r'[^a-z0-9]+', '-', prod.lower()).strip('-')
    
    if any(p["id"] == id_prod for p in estructura_final.get("productos", [])):
        print(f"⏭️ '{prod}' ya existe en la base de datos. Saltando...")
        continue

    print(f"\n⚙️ Analizando y redactando review de: {prod}...")
    
    prompt_review = f"""
    Eres un analista experto en tecnología de 'KazokuGaming'. Haz una reseña profunda de "{prod}".
    Devuelve ÚNICAMENTE un JSON estricto sin comillas markdown con esta estructura:
    {{
        "categoria": "Ej: Periféricos, Hardware, Monitores...",
        "calificacion": "Ej: 9.0",
        "descripcion_corta": "Resumen atractivo de 2 líneas para incitar a comprar.",
        "caracteristicas": ["Característica 1", "Característica 2", "Característica 3", "Característica 4"],
        "pros": ["Pro 1", "Pro 2", "Pro 3"],
        "contras": ["Contra 1", "Contra 2"],
        "analisis_profesional": "HTML con etiquetas <p> detallando rendimiento, diseño y veredicto final. Original y persuasivo.",
        "prompt_imagen": "Palabra clave en inglés muy simple para buscar imagen del producto (ej: 'gaming mouse', 'graphics card')"
    }}
    """
    
    try:
        config_rev = types.GenerateContentConfig(temperature=0.4, tools=[{"google_search": {}}])
        res = generar_con_reintentos(prompt_review, config_rev)
        data = json.loads(extraer_json_seguro(res.text))
        
        imagen_real = "https://images.unsplash.com/photo-1531297484001-80022131f5a1?q=80&w=1200"
        prompt_img = data.get("prompt_imagen", "gaming technology")
        if pexels_key:
            try:
                r = requests.get(f"https://api.pexels.com/v1/search?query={urllib.parse.quote(prompt_img)}&per_page=3", headers={"Authorization": pexels_key}, timeout=5).json()
                if r.get("photos"): imagen_real = random.choice(r["photos"])["src"]["landscape"]
            except: pass

        link_afiliado = ""
        if input_productos and i < len(links_manuales) and links_manuales[i]:
            link_afiliado = links_manuales[i]
        else:
            link_afiliado = f"https://www.amazon.es/s?k={urllib.parse.quote(prod)}&tag={TAG_AFILIADO}"
        
        nuevo_producto = {
            "id": id_prod,
            "titulo": prod,
            "fecha": time.strftime("%d %b, %Y"),
            "categoria": data.get("categoria", "Hardware"),
            "calificacion": data.get("calificacion", "8.0"),
            "descripcion_corta": data.get("descripcion_corta", "Análisis tecnológico en curso."),
            "caracteristicas": data.get("caracteristicas", []),
            "pros": data.get("pros", []),
            "contras": data.get("contras", []),
            "analisis_profesional": data.get("analisis_profesional", "<p>Datos procesados con IA.</p>"),
            "imagen": imagen_real,
            "link_compra": link_afiliado
        }
        
        estructura_final["productos"].insert(0, nuevo_producto)
        nuevos_agregados += 1
        time.sleep(5)
            
    except Exception as e:
        print(f"❌ Error procesando {prod}: {e}")

with open(archivo_oficial, "w", encoding="utf-8") as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print(f"\n✅ Base de datos 'tecnologia.json' actualizada ({nuevos_agregados} nuevos).")
