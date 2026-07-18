import os
import json
import datetime

print("=== INICIANDO GENERADOR DE SITEMAP SEO ===")

# Configura aquí tu dominio principal (el que usas en Vercel o Hostinger)
BASE_URL = "https://kazokugaming.com"

# Páginas estáticas principales
urls_estaticas = [
    "/index.html",
    "/juegos.html",
    "/noticias.html",
    "/tecnologia.html",
    "/guias.html",
    "/proyectos.html",
    "/radar.html"
]

urls_dinamicas = []

def extraer_urls(archivo_json, clave_array, ruta_html):
    if os.path.exists(archivo_json):
        with open(archivo_json, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                items = data.get(clave_array, [])
                for item in items:
                    if "id" in item:
                        urls_dinamicas.append(f"/{ruta_html}?id={item['id']}")
            except Exception as e:
                print(f"⚠️ Error leyendo {archivo_json}: {e}")

# Escanear todas las bases de datos JSON
extraer_urls("juegos.json", "juegos", "juego.html")
extraer_urls("guias.json", "guias", "guia.html")
extraer_urls("tecnologia.json", "productos", "producto.html")
extraer_urls("proyectos.json", "proyectos", "proyecto.html")
# Si tienes un JSON para artículos/noticias agrégalo aquí
extraer_urls("articulos.json", "articulos", "articulo.html")

todas_las_urls = urls_estaticas + urls_dinamicas
fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")

# Generar el contenido del XML
xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

for path in todas_las_urls:
    prioridad = "1.0" if path == "/index.html" else "0.8"
    xml_content += '  <url>\n'
    xml_content += f'    <loc>{BASE_URL}{path}</loc>\n'
    xml_content += f'    <lastmod>{fecha_actual}</lastmod>\n'
    xml_content += '    <changefreq>daily</changefreq>\n'
    xml_content += f'    <priority>{prioridad}</priority>\n'
    xml_content += '  </url>\n'

xml_content += '</urlset>'

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(xml_content)

print(f"✅ Sitemap generado exitosamente con {len(todas_las_urls)} enlaces.")
