import os
import sys
import json
import time
import re
import urllib.parse
import requests
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: ESTRATEGA DE GUÍAS (MODO MULTI-COMANDO) ===")

api_key = os.environ.get("GEMINI_API_KEY")
rawg_key = os.environ.get("RAWG_API_KEY")
comando_input = os.environ.get("INPUT_COMANDOS", "").strip().lower()

if not comando_input: comando_input = "top"
if not api_key: sys.exit("❌ ERROR: No se encontró GEMINI_API_KEY.")

client = genai.Client(api_key=api_key)
archivo_guias = "guias.json"
archivo_juegos = "juegos.json" 

datos_guias = {"guias": []}
if os.path.exists(archivo_guias):
    with open(archivo_guias, "r", encoding="utf-8") as f:
        try: datos_guias = json.load(f)
        except: pass

datos_juegos = {"juegos": []}
if os.path.exists(archivo_juegos):
    with open(archivo_juegos, "r", encoding="utf-8") as f:
        try: datos_juegos = json.load(f)
        except: pass

if comando_input.startswith("eliminar:"):
    ids_brutos = comando_input.replace("eliminar:", "", 1)
    ids_a_eliminar = [i.strip() for i in ids_brutos.split(";") if i.strip()]
    
    print(f"🗑️ COMANDO DEPURACIÓN: Intentando eliminar las guías con IDs: {ids_a_eliminar}")
    
    guias_originales = len(datos_guias.get("guias", []))
    datos_guias["guias"] = [g for g in datos_guias.get("guias", []) if g.get("id") not in ids_a_eliminar]
    guias_borradas = guias_originales - len(datos_guias["guias"])
    
    if guias_borradas > 0:
        with open(archivo_guias, "w", encoding="utf-8") as f:
            json.dump(datos_guias, f, ensure_ascii=False, indent=2)
        print(f"✅ ÉXITO: Se han eliminado {guias_borradas} guía(s) de la base de datos.")
    else:
        print("⚠️ No se encontró ninguna guía con ese ID en el registro.")
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
                if "503" in str(e).lower() or "unavailable" in str(e).lower() or "429" in str(e).lower(): continue
                raise e
        time.sleep(10)
    raise Exception("❌ Servidores de IA caídos.")

titulos_con_guia = [g.get("juego", "").lower() for g in datos_guias.get("guias", [])]
juegos_a_procesar = []

if comando_input == "top":
    print("🏆 COMANDO 'TOP': Revisando las primeras posiciones de la base de datos (Top 10)...")
    primeros_juegos = datos_juegos.get("juegos", [])[:10]
    for j in primeros_juegos:
        if j.get("titulo", "").lower() not in titulos_con_guia:
            juegos_a_procesar.append(j.get("titulo"))

elif comando_input.isdigit():
    cantidad = int(comando_input)
    print(f"🎲 COMANDO NUMÉRICO: Buscando los próximos {cantidad} juegos del catálogo sin guía táctica...")
    for j in datos_juegos.get("juegos", []):
        if j.get("titulo", "").lower() not in titulos_con_guia:
            juegos_a_procesar.append(j.get("titulo"))
            if len(juegos_a_procesar) >= cantidad:
                break

else:
    print("🛠️ COMANDO LISTA: Preparando guías para los nombres específicos solicitados...")
    # SEGURIDAD: Limpieza de inputs contra Prompt Injection
    juegos_a_procesar = [re.sub(r'["\n\r]', '', t.strip()) for t in os.environ.get("INPUT_COMANDOS", "").split(";") if t.strip()]

if not juegos_a_procesar:
    print("✅ Misión completada: No hay trabajo pendiente bajo este comando.")
    sys.exit(0)

print(f"📝 Redactando {len(juegos_a_procesar)} expedientes tácticos...")

for juego_limpio in juegos_a_procesar:
    slug = re.sub(r'[^a-z0-9]+', '-', juego_limpio.lower()).strip('-')
    id_guia = f"guia-{slug}"[:50]

    print(f"\n🔍 Investigando secretos, armas y estrategias para: {juego_limpio}...")

    prompt_sistema = f"""
    Eres el Estratega de KazokuGaming. Escribe una GUÍA TÁCTICA AVANZADA.
    Juego: "{juego_limpio}".
    Redacta con estilo analítico. Devuelve ÚNICAMENTE un JSON estricto:
    {{
      "titulo": "Guía Táctica: [Nombre]",
      "meta_descripcion": "Resumen 150 caracteres",
      "tags": ["Tag1", "Tag2"],
      "tiempo_lectura": "5 min",
      "contenido": "<h2>Análisis</h2><p>Texto...</p><h2>Mejores Estrategias o builds</h2><p>Texto...</p>",
      "seo": {{ "keywords": "palabra1, palabra2" }},
      "open_graph": {{ "og_title": "Título", "og_description": "Desc", "og_type": "article" }}
    }}
    """

    try:
        termino_busqueda = f"Guia de juego secretos trucos mejores armas {juego_limpio}".strip()
        config_guia = types.GenerateContentConfig(temperature=0.35, tools=[{"google_search": {}}])
        
        response = generar_con_reintentos(f"Redacta el dossier de: {termino_busqueda}", config_guia)
        guia_generada = json.loads(extraer_json_seguro(response.text))
        
        imagen_final = "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200"
        if rawg_key:
            try:
                r = requests.get(f"https://api.rawg.io/api/games?key={rawg_key}&search={urllib.parse.quote(juego_limpio)}&page_size=1", timeout=5).json()
                if r.get("results"): imagen_final = r["results"][0].get("background_image", imagen_final)
            except: pass
        
        guia_final = {
            "id": id_guia,
            "juego": juego_limpio,
            "titulo": guia_generada.get("titulo", f"Guía de {juego_limpio}"),
            "slug": slug,
            "categoria": "Guía Táctica",
            "tags": guia_generada.get("tags", []),
            "autor": "Kazoku Estratega",
            "imagen": imagen_final,
            "fecha": time.strftime("%d %b, %Y"),
            "tiempo_lectura": guia_generada.get("tiempo_lectura", "7 min"),
            "contenido": guia_generada.get("contenido", "<p>Expediente clasificado.</p>"),
            "meta_descripcion": guia_generada.get("meta_descripcion", "")
        }
        
        datos_guias["guias"].insert(0, guia_final)
        print(f"✅ ¡Dossier de {juego_limpio} redactado exitosamente!")
        
        with open(archivo_guias, "w", encoding="utf-8") as f:
            json.dump(datos_guias, f, ensure_ascii=False, indent=2)
            
        time.sleep(5) 

    except Exception as e:
        print(f"❌ Error al procesar la guía de {juego_limpio}: {e}")

print("\n🚀 PROCESO TÁCTICO FINALIZADO.")
