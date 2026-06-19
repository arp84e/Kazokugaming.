import os
import sys
import json
import re
from google import genai
from google.genai import types
from duckduckgo_search import DDGS

print("=== 🤖 KAZOKUBOT: MOTOR EDITORIAL DE ARTÍCULOS PRO ===")

# 📥 1. CAPTURA DE ENTRADAS DESDE GITHUB ACTIONS
accion = os.environ.get("INPUT_ACCION", "1_generar_borrador")
tema = os.environ.get("INPUT_TEMA", "")
categoria = os.environ.get("INPUT_CATEGORIA", "Tecnología")
enlaces_manuales = os.environ.get("INPUT_ENLACES", "")
imagen_ok = os.environ.get("INPUT_IMAGEN_OK", "1")
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: No se configuró GEMINI_API_KEY en los secretos del repositorio.")
    sys.exit(1)

client = genai.Client(api_key=api_key)
archivo_borrador = "articulos_borrador.json"
archivo_oficial = "articulos.json"

# Configuración de seguridad laxa para evitar censura en temas de videojuegos con acción o armas
seguridad = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

# =====================================================================
# 🔄 FASE 1: GENERAR UN NUEVO BORRADOR
# =====================================================================
if accion == "1_generar_borrador":
    if not tema:
        print("❌ ERROR: Para generar un borrador necesitas escribir un 'Tema o Título'.")
        sys.exit(1)
        
    print(f"🔎 Investigando el tema: '{tema}'...")
    contexto_busqueda = ""
    
    # 🕵️ A) Buscar en Internet usando DuckDuckGo
    try:
        with DDGS() as ddgs:
            # Busqueda enfocada a traer datos recientes y técnicos
            resultados = list(ddgs.text(f"{tema} official news specs", max_results=4))
            for res in resultados:
                contexto_busqueda += f"- {res['title']}: {res['body']} (Fuente: {res['href']})\n"
    except Exception as e:
        print(f"⚠️ Nota: No se pudo complementar con buscador externo ({e}), usaremos enlaces directos.")

    # 🔗 B) Agregar enlaces oficiales dados por el usuario
    if enlaces_manuales:
        contexto_busqueda += f"\n[FUENTES OFICIALES PRIORITARIAS INDICADAS POR EL USUARIO]:\n{enlaces_manuales}\n"

    # 🖼️ C) Buscar 3 Opciones de Imágenes atractivas en la web
    print("🖼️ Buscando opciones de imágenes impactantes...")
    opciones_imagenes = []
    try:
        with DDGS() as ddgs:
            img_results = list(ddgs.images(f"{tema} gaming wallpaper 4k", max_results=10))
            # Filtrar imágenes que parezcan rotas o URLs raras y tomar las 3 mejores
            for img in img_results:
                url = img.get('image')
                if url and url.startswith("http") and not any(x in url for x in ["thumbnail", "icon", "avatar"]):
                    opciones_imagenes.append(url)
                if len(opciones_imagenes) >= 3:
                    break
    except Exception as e:
        print(f"⚠️ Error al buscar imágenes en internet: {e}")
    
    # Si falla internet, ponemos imágenes genéricas de respaldo profesionales
    while len(opciones_imagenes) < 3:
        opciones_imagenes.append("https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200")

    # ✍️ D) Redacción del súper artículo con la IA de Gemini
    print("✍️ Redactando contenido SEO-Optimized con Gemini...")
    
    prompt = f"""
    Actúa como un Redactor Jefe Senior y experto en SEO para la revista digital KazokuGaming.
    Tu objetivo es escribir un artículo técnico, original, llamativo y muy profesional basado en los siguientes datos de investigación:
    
    TEMA DE ENTRADA: {tema}
    CATEGORÍA: {categoria}
    INVESTIGACIÓN ENCONTRADA:
    {contexto_busqueda}
    
    INSTRUCCIONES ESTRICTAS DE REDACCIÓN:
    1. TÍTULO: Debe ser sumamente profesional, con gancho clínico y optimizado para SEO (Añade palabras clave). Max 70 caracteres.
    2. RESUMEN CORTO: Un gancho de 2 líneas para mostrar en la tarjeta de la página de inicio.
    3. CUERPO (Estructura HTML Semántica y limpia):
       - No uses etiquetas <html>, <body> ni <h1>.
       - Usa únicamente párrafos (<p class="mb-4 text-justify">...</p>).
       - Usa encabezados llamativos con subtítulos en h3 (<h3 class="text-xl font-bold text-white mt-6 mb-3">Subtítulo</h3>).
       - Agrega listas ordenadas o desordenadas para especificaciones si aplica (<ul class="list-disc pl-5 space-y-1 mb-4">).
       - El tono debe ser maduro, analítico, apasionado y con un vocabulario gamer técnico excelente (habla de optimización, frames, arquitectura de hardware, narrativa, etc.).
       - Longitud: Mínimo 4 párrafos extensos y bien estructurados.
    4. CONCLUSIÓN: Termina con una breve reflexión final del analista.
    
    RESPONDE EXCLUSIVAMENTE EN EL SIGUIENTE FORMATO JSON (Sin bloques de código markdown, solo el texto JSON plano):
    {{
      "titulo": "Título profesional aquí",
      "resumen": "Resumen corto e intrigante aquí.",
      "cuerpo": "Contenido del cuerpo formateado en HTML limpio tal como se solicitó.",
      "categoria": "{categoria}"
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=seguridad, 
                response_mime_type="application/json"
            )
        )
        articulo_ia = json.loads(response.text)
    except Exception as e:
        print(f"❌ ERROR CON GEMINI: {e}")
        sys.exit(1)

    # E) Armar el archivo de borrador para que lo revises
    borrador_data = {
        "titulo": list(articulo_ia.values())[0] if "titulo" not in articulo_ia else articulo_ia["titulo"], # Salvaguarda de llaves
        "resumen": articulo_ia.get("resumen", "Previa del artículo."),
        "cuerpo": articulo_ia.get("cuerpo", ""),
        "categoria": categoria,
        "imagenes_candidatas": opciones_imagenes
    }
    
    with open(archivo_borrador, "w", encoding="utf-8") as f:
        json.dump(borrador_data, f, ensure_ascii=False, indent=2)
        
    print("\n" + "="*50)
    print("🎉 ¡BORRADOR GENERADO CON ÉXITO!")
    print(f"📝 Título sugerido: {borrador_data['titulo']}")
    print("="*50)
    print("🖼️ COPIA LAS URLS DE LAS IMÁGENES PARA REVISARLAS EN TU NAVEGADOR:")
    print(f" Opción [1]: {opciones_imagenes[0]}")
    print(f" Opción [2]: {opciones_imagenes[1]}")
    print(f" Opción [3]: {opciones_imagenes[2]}")
    print("="*50)
    print("💡 Siguientes pasos: Revisa las fotos. Si estás de acuerdo, ejecuta de nuevo este workflow seleccionando '2_publicar_borrador' y elige tu número de foto.")

# =====================================================================
# 🚀 FASE 2: APROBAR Y PUBLICAR EL BORRADOR EN PRODUCCIÓN
# =====================================================================
elif accion == "2_publicar_borrador":
    if not os.path.exists(archivo_borrador):
        print("❌ ERROR: No hay ningún borrador creado previamente. Corre primero la acción '1_generar_borrador'.")
        sys.exit(1)
        
    with open(archivo_borrador, "r", encoding="utf-8") as f:
        borrador = json.load(f)
        
    # Seleccionar la foto que elegiste
    idx_foto = int(imagen_ok) - 1
    if idx_foto < 0 or idx_foto > 2: idx_foto = 0
    imagen_final = borrador["imagenes_candidatas"][idx_foto]
    
    # Generar URL amigable para SEO (Slug)
    slug = re.sub(r'[^a-z0-9]+', '-', borrador["titulo"].lower()).strip('-')
    from datetime import datetime
    import time
    timestamp = int(time.time())
    id_final = f"art-{slug}"
    
    # Construir el nodo del nuevo artículo
    nuevo_articulo = {
        "id": id_final,
        "titulo": borrador["titulo"],
        "resumen": borrador["resumen"],
        "cuerpo": borrador["cuerpo"],
        "categoria": borrador["categoria"],
        "imagen": imagen_final,
        "fecha": datetime.now().strftime("%d %b, %Y"),
        "enlace": enlaces_manuales if enlaces_manuales else "https://kazokugaming.com"
    }
    
    # Cargar base de datos de artículos existentes
    articulos_lista = []
    if os.path.exists(archivo_oficial):
        try:
            with open(archivo_oficial, "r", encoding="utf-8") as f:
                articulos_lista = json.load(f)
                if isinstance(articulos_lista, dict):  # Si antes era un objeto, lo convertimos a lista
                    articulos_lista = articulos_lista.get("articulos", [])
        except Exception:
            articulos_lista = []
            
    # Insertar al inicio de la lista (para que aparezca de primero en la web)
    articulos_lista.insert(0, nuevo_articulo)
    
    # Guardar la base de datos oficial actualizada
    with open(archivo_oficial, "w", encoding="utf-8") as f:
        json.dump(articulos_lista, f, ensure_ascii=False, indent=2)
        
    # Limpiar el borrador ya publicado para mantener el orden
    if os.path.exists(archivo_borrador):
        os.remove(archivo_borrador)
        
    print(f"🚀 ¡BRILLANTE! El artículo '{nuevo_articulo['titulo']}' ha sido aprobado y publicado exitosamente en {archivo_oficial}.")
