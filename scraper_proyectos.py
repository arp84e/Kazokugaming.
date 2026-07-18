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

print("=== INICIANDO KAZOKUBOT: INGENIERO DE PROYECTOS DIY ===")

api_key = os.environ.get("GEMINI_API_KEY")
pexels_key = os.environ.get("PEXELS_API_KEY")
comando_input = os.environ.get("INPUT_COMANDOS", "").strip().lower()

if not comando_input: comando_input = "top"
if not api_key: sys.exit("❌ ERROR: No se encontró GEMINI_API_KEY.")

client = genai.Client(api_key=api_key)
archivo_oficial = "proyectos.json"

estructura_final = {"proyectos": []}
nombres_existentes = []
if os.path.exists(archivo_oficial):
    with open(archivo_oficial, "r", encoding="utf-8") as f:
        try: 
            estructura_final = json.load(f)
            nombres_existentes = [p["titulo"].lower() for p in estructura_final.get("proyectos", [])]
        except: pass

# ================= MÓDULO DE ELIMINACIÓN =================
if comando_input.startswith("eliminar:"):
    ids_brutos = comando_input.replace("eliminar:", "", 1)
    ids_a_eliminar = [i.strip() for i in ids_brutos.split(";") if i.strip()]
    
    prod_originales = len(estructura_final.get("proyectos", []))
    estructura_final["proyectos"] = [p for p in estructura_final.get("proyectos", []) if p.get("id") not in ids_a_eliminar]
    if (prod_originales - len(estructura_final["proyectos"])) > 0:
        with open(archivo_oficial, "w", encoding="utf-8") as f:
            json.dump(estructura_final, f, ensure_ascii=False, indent=2)
        print("✅ Proyecto(s) eliminado(s) con éxito.")
    sys.exit(0)

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
                if "503" in str(e) or "429" in str(e): continue
                else: raise e 
        time.sleep(10)
    raise Exception("❌ Servidores inactivos.")

proyectos_a_procesar = []

if comando_input == "top":
    print("🌍 Buscando los mejores proyectos DIY para Gaming/Setup...")
    prompt_top = f"""
    Eres un ingeniero experto en DIY (Hazlo tú mismo). Propón 3 proyectos tecnológicos que la gente pueda construir en casa.
    Prioridad ABSOLUTA: Proyectos orientados al Gaming (ej: Máquina Arcade con Raspberry Pi, Consola Retro portátil, Volante casero, Iluminación RGB reactiva con Arduino para la habitación, Pantallas de estadísticas de PC).
    EXCLUYE: {nombres_existentes}.
    Devuelve ÚNICAMENTE un JSON estricto: {{ "resultados": ["Proyecto 1", "Proyecto 2", "Proyecto 3"] }}
    """
    try:
        config_top = types.GenerateContentConfig(temperature=0.7, tools=[{"google_search": {}}])
        res = generar_con_reintentos(prompt_top, config_top)
        proyectos_a_procesar = json.loads(extraer_json_seguro(res.text)).get("resultados", [])
    except Exception as e: sys.exit(f"❌ Error: {e}")
elif comando_input.isdigit():
    # Lógica para números...
    pass
else:
    proyectos_a_procesar = [re.sub(r'["\n\r]', '', p.strip()) for p in os.environ.get("INPUT_COMANDOS", "").split(";") if p.strip()]

nuevos_agregados = 0

for proy in proyectos_a_procesar:
    id_proy = re.sub(r'[^a-z0-9]+', '-', proy.lower()).strip('-')
    if any(p["id"] == id_proy for p in estructura_final.get("proyectos", [])): continue

    print(f"\n⚙️ Redactando tutorial paso a paso para: {proy}...")
    
    prompt_tutorial = f"""
    Eres un instructor experto en proyectos DIY Maker (Arduino, Raspberry Pi, impresión 3D, carpintería gaming). 
    Escribe un tutorial paso a paso muy detallado y fácil de entender para crear: "{proy}".
    
    REGLA DE IMÁGENES MAGISTRAL:
    Dentro del 'contenido_html', cada vez que expliques una parte esencial (el ensamblaje, el circuito, la placa), DEBES insertar esta etiqueta exacta donde iría la foto:
    [IMAGEN: palabra_clave_en_ingles_muy_simple]
    (Ejemplos: [IMAGEN: soldering iron], [IMAGEN: raspberry pi board], [IMAGEN: rgb led strip]). Usa al menos 3 a lo largo del texto.

    Devuelve ÚNICAMENTE un JSON estricto:
    {{
        "categoria": "Ej: Raspberry Pi, Arduino, Setup Gaming, Impresión 3D",
        "dificultad": "Baja, Media o Alta",
        "tiempo_estimado": "Ej: 4 horas",
        "descripcion_corta": "Gancho de 2 líneas motivando al usuario a construirlo.",
        "materiales": ["Lista detallada", "de materiales", "y herramientas"],
        "contenido_html": "HTML con <h2>, <p> y las etiquetas [IMAGEN: keyword]. Explica paso a paso.",
        "prompt_portada": "Palabras en inglés para la foto final del proyecto (ej: 'retro arcade machine')"
    }}
    """
    
    try:
        config_tut = types.GenerateContentConfig(temperature=0.4, tools=[{"google_search": {}}])
        data = json.loads(extraer_json_seguro(generar_con_reintentos(prompt_tutorial, config_tut).text))
        
        # 1. Buscar Portada Principal
        imagen_real = "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1200"
        if pexels_key:
            try:
                r = requests.get(f"https://api.pexels.com/v1/search?query={urllib.parse.quote(data.get('prompt_portada', 'technology diy'))}&per_page=3", headers={"Authorization": pexels_key}, timeout=5).json()
                if r.get("photos"): imagen_real = random.choice(r["photos"])["src"]["landscape"]
            except: pass

        # 2. INYECCIÓN DINÁMICA DE IMÁGENES EN EL HTML
        html_crudo = data.get("contenido_html", "")
        etiquetas_imagen = set(re.findall(r'\[IMAGEN:\s*(.*?)\]', html_crudo, re.IGNORECASE))
        
        for keyword in etiquetas_imagen:
            img_paso = "https://images.unsplash.com/photo-1555680202-c86f0e12f086?q=80&w=800" # fallback hardware
            if pexels_key:
                try:
                    r = requests.get(f"https://api.pexels.com/v1/search?query={urllib.parse.quote(keyword.strip())}&per_page=1", headers={"Authorization": pexels_key}, timeout=5).json()
                    if r.get("photos"): img_paso = r["photos"][0]["src"]["landscape"]
                except: pass
            
            tag_html = f'<img src="{img_paso}" alt="Ilustración paso: {keyword}" class="w-full object-cover rounded-2xl shadow-[0_0_15px_rgba(139,92,246,0.2)] my-8 border border-slate-700/50">'
            html_crudo = re.sub(rf'\[IMAGEN:\s*{re.escape(keyword)}\]', tag_html, html_crudo, flags=re.IGNORECASE)
            time.sleep(1) # Respetar límite de Pexels

        nuevo_proy = {
            "id": id_proy,
            "titulo": proy,
            "fecha": time.strftime("%d %b, %Y"),
            "categoria": data.get("categoria", "DIY Gaming"),
            "dificultad": data.get("dificultad", "Media"),
            "tiempo_estimado": data.get("tiempo_estimado", "Varias horas"),
            "descripcion_corta": data.get("descripcion_corta", "Construye tu propio setup paso a paso."),
            "materiales": data.get("materiales", []),
            "contenido_html": html_crudo,
            "imagen": imagen_real
        }
        
        estructura_final["proyectos"].insert(0, nuevo_proy)
        nuevos_agregados += 1
            
    except Exception as e:
        print(f"❌ Error en {proy}: {e}")

with open(archivo_oficial, "w", encoding="utf-8") as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print(f"\n✅ Base 'proyectos.json' actualizada ({nuevos_agregados} nuevos).")
