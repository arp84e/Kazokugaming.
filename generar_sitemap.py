# generar_sitemap.py - Generador automático de Sitemap para KazokuGaming
import json
import os
import time

DOMINIO = "https://kazokugaming.com" # Modifica por tu dominio final si es distinto

def crear_sitemap():
    print("🗺️ Reconstruyendo sitemap.xml...")
    urls = [
        "", 
        "/juegos.html",
        "/guias.html",
        "/noticias.html",
        "/radar.html",
        "/tecnologia.html"
    ]
    
    # Añadir enlaces dinámicos de Artículos (Noticias)
    if os.path.exists("articulos.json"):
        with open("articulos.json", "r", encoding="utf-8") as f:
            try:
                articulos = json.load(f)
                if isinstance(articulos, dict): articulos = articulos.get("articulos", [])
                for a in articulos:
                    urls.append(f"/articulo.html?id={a['id']}")
            except: pass

    # Añadir enlaces dinámicos del Top 10 y Directorio de Juegos
    if os.path.exists("juegos.json"):
        with open("juegos.json", "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                juegos = data.get("juegos", [])
                for j in juegos:
                    urls.append(f"/juego.html?id={j['id']}")
            except: pass

    # Añadir enlaces dinámicos de las Guías
    if os.path.exists("guias.json"):
        with open("guias.json", "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                guias = data.get("guias", [])
                for g in guias:
                    urls.append(f"/guia.html?id={g['id']}")
            except: pass

    # Añadir enlaces dinámicos de Hardware y Tecnología
    if os.path.exists("tecnologia.json"):
        with open("tecnologia.json", "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                tecnologia = data.get("productos", [])
                for t in tecnologia:
                    urls.append(f"/producto.html?id={t['id']}")
            except: pass

    fecha_hoy = time.strftime("%Y-%m-%d")
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url in urls:
        # Escapar el ampersand si existiera en algún ID o parámetro
        url_escaped = url.replace("&", "&amp;") 
        prioridad = "1.0" if url == "" else ("0.8" if "?" not in url else "0.6")
        
        xml_content += f'  <url>\n'
        xml_content += f'    <loc>{DOMINIO}{url_escaped}</loc>\n'
        xml_content += f'    <lastmod>{fecha_hoy}</lastmod>\n'
        xml_content += f'    <changefreq>daily</changefreq>\n'
        xml_content += f'    <priority>{prioridad}</priority>\n'
        xml_content += f'  </url>\n'
        
    xml_content += '</urlset>'
    
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
        
    print(f"✅ Sitemap actualizado exitosamente con {len(urls)} enlaces indexados.")

if __name__ == "__main__":
    crear_sitemap()
