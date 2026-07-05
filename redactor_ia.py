import os
import json
import time
import re
from google import genai
from google.genai import types

print("=== INICIANDO KAZOKUBOT: REDACTOR EN JEFE IA ===")

# 1. Configuración de API y Archivo
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY en las variables de entorno.")
    exit(1)

client = genai.Client(api_key=api_key)
archivo_articulos = "articulos.json"

# 2. Tu lista de temas a redactar (Puedes poner 10, 20 o 50 temas aquí)
temas_a_redactar = [
    {"tema": "Los mejores monitores OLED para PS5 y Xbox Series X en 2026", "categoria": "Hardware"},
    {"tema": "Análisis profundo de la nueva arquitectura de Unreal Engine 6", "categoria": "Tecnología"},
    {"tema": "Cómo la Inteligencia Artificial está cambiando el diseño de niveles en los videojuegos", "categoria": "Inteligencia Artificial"}
]

# 3. Cargar la base de datos existente
datos_web = {"articulos": []}
if os.path.exists(archivo_articulos):
    with open(archivo_articulos, "r", encoding="utf-8") as f:
        try:
            datos_web = json.load(f)
        except Exception as e:
            print(f"⚠️ Aviso: No se pudo leer el JSON previo. Se creará uno nuevo. Error: {e}")

# 4. El Prompt Maestro (El "Cerebro" del Periodista)
prompt_sistema = """
Eres un periodista tecnológico y de videojuegos experto de 'KazokuGaming'.
Tu estilo es profesional, analítico, directo y con un tono táctico/entusiasta.
Escribe un artículo completo y optimizado para SEO sobre el tema proporcionado.

REGLAS DE FORMATO ESTRICTAS:
1. Debes devolver ÚNICAMENTE un objeto JSON válido.
2. El campo 'contenido' debe estar en formato HTML limpio usando <p class='mb-4'> para párrafos, <h3 class='text-xl font-bold text-cyan-400 mt-8 mb-4'> para subtítulos, y <strong> para resaltar texto. No uses Markdown dentro del HTML.
3. Genera un mínimo de 3 subtítulos detallados.
4. Para la 'imagen', genera una URL de Unsplash representativa usando este formato: https://images.unsplash.com/photo-[ID-ALEATORIO]?q=80&w=1200&auto=format&fit=crop&query=[tu-palabra-clave-en-ingles]

ESTRUCTURA JSON REQUERIDA:
{
  "titulo": "Título SEO atractivo y clickbait pero profesional",
  "meta_descripcion": "Resumen de 150 caracteres para Google",
  "tags": ["Tag1", "Tag2", "Tag3", "Tag4"],
  "tiempo_lectura": "X min",
  "imagen": "URL de Unsplash generada",
  "contenido": "Todo el HTML aquí"
}
"""

# 5. Bucle de Redacción Automatizada
for item in temas_a_redactar:
    tema = item["tema"]
    categoria = item["categoria"]
    
    # Generar un ID único basado en el tema
    slug = re.sub(r'[^a-z0-9]+', '-', tema.lower()).strip('-')
    id_articulo = f"art-{slug}"[:50] # Limitamos la longitud del ID
    
    # Verificar si el artículo ya existe para no duplicarlo
    if any(art["id"] == id_articulo for art in datos_web["articulos"]):
        print(f"⏭️ Saltando: '{tema}' (Ya existe).")
        continue

    print(f"✍️ Redactando artículo: {tema}...")
    
    try:
        # Llamada a la IA (Forzando la salida en JSON puro)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Tema a redactar: {tema}",
            config=types.GenerateContentConfig(
                system_instruction=prompt_sistema,
                response_mime_type="application/json",
                temperature=0.7 # Equilibrio entre creatividad y precisión
            )
        )
        
        # Procesar la respuesta
        articulo_generado = json.loads(response.text)
        
        # Ensamblar el artículo final con los datos fijos
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
        
        # Añadir a la base de datos
        datos_web["articulos"].insert(0, articulo_final) # Lo inserta al principio (más reciente)
        print(f"✅ ¡Artículo guardado con éxito!")
        
        # SISTEMA ANTI-COLAPSO: Espera de 15 segundos entre artículos
        # Es crítico para evitar el error "RESOURCE_EXHAUSTED" si generas decenas de artículos
        print("⏳ Pausa de enfriamiento de la API (15s)...")
        time.sleep(15)

    except Exception as e:
        print(f"❌ Error al generar '{tema}': {e}")
        # Pausa extra de seguridad si hay error
        time.sleep(30)

# 6. Guardar todo en el archivo articulos.json
with open(archivo_articulos, "w", encoding="utf-8") as f:
    json.dump(datos_web, f, ensure_ascii=False, indent=2)

print("\n🚀 ¡PROCESO FINALIZADO! La base de datos de artículos ha sido actualizada.")
