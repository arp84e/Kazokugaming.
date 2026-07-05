import os
import json
import time
import re
import random
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

temas_a_redactar = [{"tema": t.strip(), "categoria": "Noticias"} for t in temas_input.split(";") if t.strip()]

# 3. Galería de imágenes reales y verificadas (Gaming, Tech, Hardware)
imagenes_reales = [
    "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200", # Setup Gaming
    "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1200", # Retro/Neon Gaming
    "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?q=80&w=1200", # Mando / Consola
    "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?q=80&w=1200", # Teclado PC RGB
    "https://images.unsplash.com/photo-1612287230202-1ff1d85d1e4e?q=80&w=1200", # Mando PS5
    "https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=1200", # Gafas VR
    "https://images.unsplash.com/photo-1552820728-8b83bb6b773f?q=80&w=1200", # Hardware / Placa Base
    "https://images.unsplash.com/photo-1600861194942-f884bfb03658?q=80&w=1200", # Neon Tech
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=1200", # Código / IA
    "https://images.unsplash.com/photo-1587202372634-32705e3bf49c?q=80&w=1200"  # Tarjeta Gráfica
]

# 4. Cargar la base de datos existente
datos_web = {"articulos": []}
if os.path.exists(archivo_articulos):
    with open(archivo_articulos, "r", encoding="utf-8") as f:
        try:
            datos_web = json.load(f)
        except Exception as e:
            print(f"⚠️ Aviso: No se pudo leer el JSON previo. Error: {e}")

# 5. El Prompt Maestro (Sin pedirle que invente URLs)
prompt_sistema = """
Eres un periodista tecnológico y de videojuegos experto de 'KazokuGaming'.
Tu estilo es profesional, analítico, directo y con un tono táctico/entusiasta.
Escribe un artículo completo y optimizado para SEO sobre el tema proporcionado.

REGLAS DE FORMATO ESTRICTAS:
1. Debes devolver ÚNICAMENTE un objeto JSON válido.
2. El campo 'contenido' debe estar en formato HTML limpio usando <p class='mb-4'> para párrafos, <h3 class='text-xl font-bold text-cyan-400 mt-8 mb-4'> para subtítulos, y <strong> para resaltar texto. No uses Markdown dentro del HTML.
3. Genera un mínimo de 3 subtítulos detallados.

ESTRUCTURA JSON REQUERIDA:
{
  "titulo": "Título SEO atractivo pero profesional",
  "meta_descripcion": "Resumen de 150 caracteres para Google",
  "tags": ["Tag1", "Tag2", "Tag3"],
  "tiempo_lectura": "X min",
  "contenido": "Todo el HTML aquí"
}
"""

# 6. Bucle de Redacción Automatizada
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
            model='gemini-3.5-flash',
            contents=f"Tema a redactar: {tema}",
            config=types.GenerateContentConfig(
                system_instruction=prompt_sistema,
                response_mime_type="application/json",
                temperature=0.7
            )
        )
        
        articulo_generado = json.loads(response.text)
        
        # Seleccionar una imagen real al azar de nuestra galería
        imagen_asignada = random.choice(imagenes_reales)
        
        articulo_final = {
            "id": id_articulo,
            "titulo": articulo_generado["titulo"],
            "slug": slug,
            "categoria": categoria,
            "tags": articulo_generado["tags"],
            "autor": "KazokuBot IA",
            "imagen": imagen_asignada,
            "fecha": time.strftime("%d %b, %Y"),
            "tiempo_lectura": articulo_generado["tiempo_lectura"],
            "meta_descripcion": articulo_generado["meta_descripcion"],
            "contenido": articulo_generado["contenido"]
        }
        
        datos_web["articulos"].insert(0, articulo_final)
        print(f"✅ ¡Artículo guardado con éxito y con imagen verificada!")
        
        print("⏳ Pausa de enfriamiento (15s)...")
        time.sleep(15)

    except Exception as e:
        print(f"❌ Error al generar '{tema}': {e}")
        time.sleep(30)

# 7. Guardar todo en el archivo
with open(archivo_articulos, "w", encoding="utf-8") as f:
    json.dump(datos_web, f, ensure_ascii=False, indent=2)

print("\n🚀 ¡PROCESO FINALIZADO! Artículos actualizados.")
