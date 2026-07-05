import os
import json
import time
import re
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: REDACTOR EN JEFE IA ===")

# 1. Configuración de API
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY.")
    exit(1)

client = genai.Client(api_key=api_key)
archivo_articulos = "articulos.json"

# 2. Leer los temas desde GitHub Actions
temas_input = os.environ.get("INPUT_TEMAS", "")
if not temas_input:
    print("❌ ERROR: No se escribieron temas para redactar.")
    exit(1)

# Separar los temas por punto y coma (;) y asignarles una categoría por defecto
temas_a_redactar = [{"tema": t.strip(), "categoria": "Noticias"} for t in temas_input.split(";") if t.strip()]

# 3. Cargar la base de datos existente
datos_web = {"articulos": []}
if os.path.exists(archivo_articulos):
    with open(archivo_articulos, "r", encoding="utf-8") as f:
        try:
            datos_web = json.load(f)
        except Exception as e:
            print(f"⚠️ Aviso: No se pudo leer el JSON previo. Error: {e}")

# 4. El Prompt Maestro
prompt_sistema = """
Eres un periodista tecnológico y de videojuegos experto de 'KazokuGaming'.
Tu estilo es profesional, analítico, directo y con un tono táctico/entusiasta.
Escribe un artículo completo y optimizado para SEO sobre el tema proporcionado.

REGLAS DE FORMATO ESTRICTAS:
1. Debes devolver ÚNICAMENTE un objeto JSON válido.
2. El campo 'contenido' debe estar en formato HTML limpio usando <p class='mb-4'> para párrafos, <h3 class='text-xl font-bold text-cyan-400 mt-8 mb-4'> para subtítulos, y <strong> para resaltar texto. No uses Markdown dentro del HTML.
3. Genera un mínimo de 3 subtítulos detallados.
4. Para la 'imagen', genera una URL de Unsplash representativa usando este formato: https://images.unsplash.com/photo-[ID-ALEATORIO]?q=80&w=1200&auto=format&fit=crop&query=[tu-palabra-clave-en-ingles-muy-corta]

ESTRUCTURA JSON REQUERIDA:
{
  "titulo": "Título SEO atractivo pero profesional",
  "meta_descripcion": "Resumen de 150 caracteres para Google",
  "tags": ["Tag1", "Tag2", "Tag3"],
  "tiempo_lectura": "X min",
  "imagen": "URL de Unsplash generada",
  "contenido": "Todo el HTML aquí"
}
"""

# 5. Bucle de Redacción Automatizada
for item in temas_a_redactar:
    tema = item["tema"]
    categoria = item["categoria"]
    
    slug = re.sub(r'[^a-z0-9]+', '-', tema.lower()).strip('-')
    id_articulo = f"art-{slug}"[:50]
    
    if any(art["id"] == id_articulo for art in datos_web["articulos"]):
        print(f"⏭️ Saltando: '{tema}' (Ya existe).")
        continue

    print(f"✍️ Redactando artículo: {tema}...")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Tema a redactar: {tema}",
            config=types.GenerateContentConfig(
                system_instruction=prompt_sistema,
                response_mime_type="application/json",
                temperature=0.7
            )
        )
        
        articulo_generado = json.loads(response.text)
        
        articulo_final = {
            "id": id_articulo,
            "titulo": articulo_generado["titulo"],
            "slug": slug,
            "categoria": categoria,
            "tags": articulo_generado["tags"],
            "autor": "KazokuBot IA",
            "imagen": articulo_generado["imagen"],
            "fecha": time.strftime("%d %b, %Y"),
            "tiempo_lectura": articulo_generado["tiempo_lectura"],
            "meta_descripcion": articulo_generado["meta_descripcion"],
            "contenido": articulo_generado["contenido"]
        }
        
        datos_web["articulos"].insert(0, articulo_final)
        print(f"✅ ¡Artículo guardado con éxito!")
        
        print("⏳ Pausa de enfriamiento (15s)...")
        time.sleep(15)

    except Exception as e:
        print(f"❌ Error al generar '{tema}': {e}")
        time.sleep(30)

# 6. Guardar todo en el archivo
with open(archivo_articulos, "w", encoding="utf-8") as f:
    json.dump(datos_web, f, ensure_ascii=False, indent=2)

print("\n🚀 ¡PROCESO FINALIZADO! Artículos actualizados.")
