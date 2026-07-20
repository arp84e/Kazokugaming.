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
from pydantic import BaseModel
from typing import List

print("=== INICIANDO KAZOKUBOT: INGENIERO MAKER (VERSIÓN MAESTRA CON ESQUEMAS) ===")

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

if comando_input.startswith("eliminar:"):
    ids_a_eliminar = [i.strip() for i in comando_input.replace("eliminar:", "", 1).split(";") if i.strip()]
    prod_originales = len(estructura_final.get("proyectos", []))
    estructura_final["proyectos"] = [p for p in estructura_final.get("proyectos", []) if p.get("id") not in ids_a_eliminar]
    if (prod_originales - len(estructura_final["proyectos"])) > 0:
        with open(archivo_oficial, "w", encoding="utf-8") as f: json.dump(estructura_final, f, ensure_ascii=False, indent=2)
        print("✅ Proyecto(s) eliminado(s) con éxito.")
    sys.exit(0)

# --- MODELOS DE DATOS (GARANTIZAN UN FORMATO IMPERMEABLE) ---
class ListaProyectos(BaseModel):
    resultados: List[str]

class ManualMaker(BaseModel):
    categoria: str
    dificultad: str
    tiempo_estimado: str
    costo_estimado: str
    requisitos_conocimiento: str
    descripcion_corta: str
    advertencias_seguridad: List[str]
    materiales: List[str]
    herramientas: List[str]
    contenido_html: str
    portada_prompt: str

def generar_con_reintentos(prompt_texto, config_ia, max_intentos=3):
    for intento in range(max_intentos):
        for modelo in ['gemini-2.5-flash', 'gemini-3.5-flash']:
            try: return client.models.generate_content(model=modelo, contents=prompt_texto, config=config_ia)
            except Exception as e:
                if "503" in str(e) or "429" in str(e): continue
                raise e 
        time.sleep(10)
    raise Exception("❌ Servidores inactivos.")

proyectos_a_procesar = []

if comando_input == "top":
    print("🌍 Buscando los mejores proyectos DIY para Gaming/Setup...")
    prompt_top = f"""
    Eres un ingeniero experto en DIY. Propón 3 proyectos tecnológicos nivel EXPERTO.
    EXCLUYE: {nombres_existentes}.
    """
    config_top = types.GenerateContentConfig(
        temperature=0.7, 
        response_mime_type="application/json",
        response_schema=ListaProyectos,
        tools=[{"google_search": {}}]
    )
    res_top = generar_con_reintentos(prompt_top, config_top)
    datos_top = json.loads(res_top.text)
    proyectos_a_procesar = datos_top.get("resultados", [])
else:
    proyectos_a_procesar = [re.sub(r'["\n\r]', '', p.strip()) for p in os.environ.get("INPUT_COMANDOS", "").split(";") if p.strip()]

nuevos_agregados = 0

for proy in proyectos_a_procesar:
    id_proy = re.sub(r'[^a-z0-9]+', '-', proy.lower()).strip('-')
    if any(p["id"] == id_proy for p in estructura_final.get("proyectos", [])): continue

    print(f"\n⚙️ Redactando MANUAL DE INGENIERÍA EXHAUSTIVO para: {proy}...")
    
    prompt_tutorial = f"""
    Eres un Ingeniero Electrónico, Programador y Creador Maker. Tu misión es redactar el MANUAL DEFINITIVO para construir: "{proy}".
    El nivel de detalle debe ser insano, pensado para que alguien sin experiencia no se pierda, pero con rigor técnico.

    REGLAS DE REDACCIÓN:
    1. EXTENSIÓN: Mínimo 1500 palabras estructuradas con etiquetas <h2> y <h3>.
    2. CÓDIGO: Si usa Arduino, Python, ROS o C++, INCLUYE LOS SCRIPTS EXACTOS usando <pre><code> ... </code></pre>.
    3. ALERTAS: Usa <blockquote> para notas de seguridad.
    4. IMÁGENES: Usa la etiqueta [IMAGEN: keyword_en_ingles_simple] al menos 6 veces.
    """
    
    try:
        # Configuración blindada con el esquema Pydantic
        config_tut = types.GenerateContentConfig(
            temperature=0.4, 
            max_output_tokens=8192, 
            response_mime_type="application/json",
            response_schema=ManualMaker,
            tools=[{"google_search": {}}]
        )
        res = generar_con_reintentos(prompt_tutorial, config_tut)
        
        # Como usamos un esquema estructurado, la respuesta es 100% JSON válido de forma nativa
        data = json.loads(res.text)
        
        imagen_real = "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1200"
        if pexels_key:
            try:
                r = requests.get(f"https://api.pexels.com/v1/search?query={urllib.parse.quote(data.get('portada_prompt', 'circuit board'))}&per_page=1", headers={"Authorization": pexels_key}, timeout=5).json()
                if r.get("photos"): imagen_real = r["photos"][0]["src"]["landscape"]
            except: pass

        html_crudo = data.get("contenido_html", "")
        etiquetas_imagen = set(re.findall(r'\[IMAGEN:\s*(.*?)\]', html_crudo, re.IGNORECASE))
        
        for keyword in etiquetas_imagen:
            img_paso = "https://images.unsplash.com/photo-1555680202-c86f0e12f086?q=80&w=800"
            if pexels_key:
                try:
                    r = requests.get(f"https://api.pexels.com/v1/search?query={urllib.parse.quote(keyword.strip())}&per_page=1", headers={"Authorization": pexels_key}, timeout=5).json()
                    if r.get("photos"): img_paso = r["photos"][0]["src"]["landscape"]
                except: pass
            
            tag_html = f'<div class="my-10"><img src="{img_paso}" alt="Paso: {keyword}" class="w-full object-cover rounded-2xl shadow-[0_0_20px_rgba(14,165,233,0.15)] border border-sky-900/40"><p class="text-center text-[11px] text-slate-500 font-mono mt-2 uppercase tracking-widest">Referencia visual: {keyword}</p></div>'
            html_crudo = re.sub(rf'\[IMAGEN:\s*{re.escape(keyword)}\]', tag_html, html_crudo, flags=re.IGNORECASE)
            time.sleep(1)

        nuevo_proy = {
            "id": id_proy,
            "titulo": proy,
            "fecha": time.strftime("%d %b, %Y"),
            "categoria": data.get("categoria", "DIY Avanzado"),
            "dificultad": data.get("dificultad", "Intermedio"),
            "tiempo_estimado": data.get("tiempo_estimado", "Varios días"),
            "costo_estimado": data.get("costo_estimado", "Variable"),
            "requisitos_conocimiento": data.get("requisitos_conocimiento", "Básicos"),
            "descripcion_corta": data.get("descripcion_corta", "Construye tu propio setup paso a paso."),
            "advertencias_seguridad": data.get("advertencias_seguridad", []),
            "materiales": data.get("materiales", []),
            "herramientas": data.get("herramientas", []),
            "contenido_html": html_crudo,
            "imagen": imagen_real
        }
        
        estructura_final["proyectos"].insert(0, nuevo_proy)
        nuevos_agregados += 1
            
    except Exception as e:
        print(f"❌ Error crítico procesando {proy}: {e}")
        continue

with open(archivo_oficial, "w", encoding="utf-8") as f:
    json.dump(estructura_final, f, ensure_ascii=False, indent=2)

print(f"\n✅ Base de proyectos actualizada con manuales exhaustivos ({nuevos_agregados} nuevos).")
