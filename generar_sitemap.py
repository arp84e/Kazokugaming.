import json
import os
import time

DOMINIO = "https://kazokugaming.com"

def crear_sitemap():
    print("🗺️ Reconstruyendo sitemap.xml...")
    urls = [
        "", 
        "/noticias.html",
        "/telemetria.html",
        "/guias.html",
        "/radar.html"
    ]
    
    if os.path.exists("articulos.json"):
        with open("articulos.json", "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for a in data.get("articulos", []):
                    urls.append(f"/articulo.html?id={a['id']}")
            except: pass

    if os.path.exists("telemetria.json"):
        with open("telemetria.json", "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for j in data.get("juegos", []):
                    urls.append(f"/juego.html?id={j['id']}")
            except: pass

    if os.path.exists("guias.json"):
        with open("guias.json", "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for g in data.get("guias", []):
                    urls.append(f"/guia.html?id={g['id']}")
            except: pass

    fecha_hoy = time.strftime("%Y-%m-%d")
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url in urls:
        prioridad = "1.0" if url == "" else ("0.8" if ".html" in url and "?" not in url else "0.6")
        xml_content += f'  <url>\n'
        xml_content += f'    <loc>{DOMINIO}{url.replace("&", "&amp;")}</loc>\n'
        xml_content += f'    <lastmod>{fecha_hoy}</lastmod>\n'
        xml_content += f'    <changefreq>daily</changefreq>\n'
        xml_content += f'    <priority>{prioridad}</priority>\n'
        xml_content += f'  </url>\n'
        
    xml_content += '</urlset>'
    
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
    print("🚀 ¡sitemap.xml actualizado con éxito para rastreadores!")

if __name__ == "__main__":
    crear_sitemap()
