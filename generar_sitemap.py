# generar_sitemap.py - Generador automático de Sitemap para KazokuGaming
import json
import os
import time

DOMINIO = "https://kazokugaming.com" # Modifica por tu dirección final adquirida

def crear_sitemap():
    print("🗺️ Reconstruyendo sitemap.xml...")
    urls = [
        "", 
        "/telemetria.html",
        "/hardware.html",
        "/radar.html",
        "/foro.html"
    ]
    
    if os.path.exists("articulos.json"):
        with open("articulos.json", "r", encoding="utf-8") as f:
            try:
                articulos = json.load(f)
                if isinstance(articulos, dict): articulos = articulos.get("articulos", [])
                for a in articulos:
                    slug = a["id"].replace("art-", "")
                    urls.append(f"/articulos/{slug}.html")
            except: pass

    if os.path.exists("telemetria.json"):
        with open("telemetria.json", "r", encoding="utf-8") as f:
            try:
                telemetria = json.load(f)
                juegos = telemetria.get("juegos", [])
                for j in juegos:
                    urls.append(f"/telemetria/{j['id']}.html")
            except: pass

    fecha_hoy = time.strftime("%Y-%m-%d")
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url in urls:
        prioridad = "1.0" if url == "" else ("0.8" if not "/" in url[1:] else "0.6")
        xml_content += f'  <url>\n'
        xml_content += f'    <loc>{DOMINIO}{url}</loc>\n'
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
