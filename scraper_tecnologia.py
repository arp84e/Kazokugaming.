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

print("=== INICIANDO KAZOKUBOT: GURÚ DE VENTAS Y HARDWARE ===")

# --- CONFIGURA AQUÍ TU TAG DE AFILIADO DE AMAZON ---
TAG_AFILIADO = "kazokugaming-21" 

api_key = os.environ.get("GEMINI_API_KEY")
pexels_key = os.environ.get("PEXELS_API_KEY")
input_productos = os.environ.get("INPUT_PRODUCTOS", "").strip()
input_links = os.environ.get("INPUT_LINKS", "").strip()

if not api_key: sys.exit("❌ ERROR: No se encontró GEMINI_API_KEY.")
client = genai.Client(api_key=api_key)
archivo_oficial = "tecnologia.json"

estructura_final = {"productos": []}
nombres_existentes = []
if os.path.exists(archivo_oficial):
    with open(archivo_oficial, "r", encoding="utf-8") as f:
        try: 
            estructura_final = json.load(f)
            nombres_existentes = [p["titulo"].lower() for p in estructura_final.get("productos", [])]
        except: pass

# ================= MÓDULO DE ELIMINACIÓN =================
if input_productos.lower().startswith("eliminar:"):
    ids_brutos = input_productos[9:]
    ids_a_eliminar = [i.strip() for i in ids_brutos.split(";") if i.strip()]
    
    print(f"🗑️ Intentando eliminar los IDs: {ids_a_eliminar}")
    
    prod_originales = len(estructura_final.get("productos", []))
    estructura_final["productos"] = [p for p in estructura_final.get("productos", []) if p.get("id") not in ids_a_eliminar]
    prod_borrados = prod_originales - len(estructura_final["productos"])
    
    if prod_borrados > 0:
        with open(archivo_oficial, "w", encoding="utf-8") as f:
            json.dump(estructura_final, f, ensure_ascii=False, indent=2)
        print(f"✅ Se han eliminado {prod_borrados} producto(s).")
    else:
        print("⚠️ No se encontró ningún producto con ese ID.")
    sys.exit(0)

# ================= MÓDULO DE REDACCIÓN DE VENTAS =================
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
                if "503" in str(e) or "unavailable" in str(e) or "429" in str(e): continue
                else: raise e 
        time.sleep(10)
    raise Exception("❌ Servidores inactivos.")

productos_a_procesar = []
links_manuales = []

if input_productos:
    print("🛠️ MODO MANUAL: Procesando catálogo específico...")
    # Sanitización de inputs contra inyecciones de prompt
    productos_a_procesar = [re.sub(r'["\n\r]', '', p.strip()) for p in input_productos.split(";") if p.strip()]
    links_manuales = [re.sub(r'["\n\r]', '', l.strip()) for l in input_links.split(";")] if input_links else []
else:
    print("🌍 MODO AUTOMÁTICO: Escaneando tendencias hiper-rentables (Hardware, Gadgets)...")
    prompt_top = f"""
    Eres un estratega de e-commerce y experto en hardware gaming. Busca en internet 3 productos tecnológicos (periféricos, componentes, monitores) que estén siendo un éxito de ventas o en súper tendencia hoy.
    EXCLUYE: {nombres_existentes}.
    Devuelve ÚNICAMENTE un JSON estricto:
    {{ "resultados": ["Producto 1", "Producto 2", "Producto 3"] }}
    """
    try:
        config_top = types.GenerateContentConfig(temperature=0.7, tools=[{"google_search": {}}])
        res_top = generar_con_reintentos(prompt_top, config_top)
        data_top = json.loads(extraer_json_seguro(res_top.text))
        productos_a_procesar = data_top.get("resultados", [])
        print(f"📡 Tendencias de mercado detectadas: {productos_a_procesar}")
    except Exception as e:
        sys.exit(f"❌ Error al buscar tendencias: {e}")

nuevos_agregados = 0

for i, prod in enumerate(productos_a_procesar):
    id_prod = re.sub(r'[^a-z0-9]+', '-', prod.lower()).strip('-')
    
    if any(p["id"] == id_prod for p in estructura_final.get("productos", [])):
        print(f"⏭️ '{prod}' ya está en el catálogo. Saltando...")
        continue

    print(f"\n⚙️ Aplicando ingeniería de ventas y copywriting para: {prod}...")
    
    # EL SECRETO DE LAS VENTAS: El System Prompt
    prompt_review = f"""
    Eres un Copywriter experto en ventas digitales y un Gurú del Hardware. 
    Tu objetivo es reseñar el producto "{prod}" y convencer al lector de que es una inversión necesaria para mejorar su rendimiento (gaming o productividad).
    Usa la fórmula PAS (Problema, Agitación, Solución) y cierra con urgencia.
    
    REGLAS DE COPYWRITING:
    - La 'descripcion_corta' debe ser un GANCHO brutal que despierte curiosidad.
    - El 'analisis_profesional' (en HTML con <p> y <strong>) debe identificar el dolor del usuario (ej: lag, baja precisión, postura, cuellos de botella), explicar cómo este producto lo soluciona, justificar su precio y empujar sutilmente a la compra.
    
    Devuelve ÚNICAMENTE un JSON estricto sin backticks de markdown:
    {{
        "categoria": "Ej: Periféricos, Componentes, Monitores",
        "calificacion": "Ej: 9.2 (Sé realista pero entusiasta)",
        "descripcion_corta": "Gancho de 2 líneas enfocado en el beneficio principal.",
        "caracteristicas": ["Spec 1", "Spec 2", "Spec 3", "Spec 4"],
        "pros": ["Beneficio clave 1", "Beneficio clave 2", "Beneficio clave 3"],
        "contras": ["Un contra menor para dar credibilidad", "Otro contra"],
        "analisis_profesional": "HTML persuasivo. Usa storytelling, destaca por qué es superior a la competencia y termina sugiriendo verificar el precio actual.",
        "prompt_imagen": "Palabras en inglés muy simples para buscar la foto (ej: 'gaming keyboard', 'pc motherboard')"
    }}
    """
    
    try:
        config_rev = types.GenerateContentConfig(temperature=0.5, tools=[{"google_search": {}}])
        res = generar_con_reintentos(prompt_review, config_rev)
        data = json.loads(extraer_json_seguro(res.text))
        
        imagen_real = "https://images.unsplash.com/photo-1531297484001-80022131f5a1?q=80&w=1200"
        prompt_img = data.get("prompt_imagen", "modern technology hardware")
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
            "categoria": data.get("categoria", "Hardware Pro"),
            "calificacion": data.get("calificacion", "8.5"),
            "descripcion_corta": data.get("descripcion_corta", "Descubre por qué este hardware está cambiando las reglas del juego."),
            "caracteristicas": data.get("caracteristicas", []),
            "pros": data.get("pros", []),
            "contras": data.get("contras", []),
            "analisis_profesional": data.get("analisis_profesional", "<p>Análisis en profundidad no disponible por el momento.</p>"),
            "imagen": imagen_real,
            "link_compra": link_afiliado
        }
        
        estructura_final["productos"].insert(0, nuevo_producto)
        nuevos_agregados += 1
        time.sleep(5)
            
    except Exception as e:
        print(f"❌ Error al aplicar copywriting en {prod}: {e}")

with open(archivo_oficial, "w", encoding="utf-8") as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print(f"\n✅ Catálogo 'tecnologia.json' actualizado ({nuevos_agregados} activos de venta generados).")
