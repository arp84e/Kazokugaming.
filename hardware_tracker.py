# -*- coding: utf-8 -*-
"""
KazokuGaming - Robot Automatizado de Monitoreo de Hardware v1.2 (Año 2026)
"""

import json
import os
from datetime import datetime

JSON_FILE = "hardware.json"

# Base de datos con las 9 laptops gaming clasificadas por gamas (baja, media, alta)
HARDWARE_BASE = {
    # === GAMA DE ENTRADA / BAJA ===
    "lenovo-loq-15": {
        "title": "Lenovo LOQ 15",
        "brand": "Lenovo",
        "category": "laptop",
        "tier": "baja",
        "desc": "El nuevo rey de la gama de entrada. Hereda la excelente distribución térmica y el teclado de la mítica línea Legion, recortando costes sutilmente en el chasis de plástico.",
        "priceUS": "$849 USD",
        "priceEU": "899 € (IVA incl.)",
        "specs": [
            {"label": "Procesador", "value": "AMD Ryzen 5 8645HS / Intel i5-13450HX"},
            {"label": "Gráfica", "value": "NVIDIA GeForce RTX 4050 Laptop (95W TGP)"},
            {"label": "Pantalla", "value": "15.6\" FHD (1080p) IPS, 144Hz"}
        ],
        "pros": ["Excelente relación calidad-precio.", "Teclado muy cómodo para su precio.", "Buenas temperaturas."],
        "contras": ["Chasis completamente de plástico.", "Batería algo justa (60Wh)."]
    },
    "asus-tuf-a15": {
        "title": "ASUS TUF Gaming A15",
        "brand": "ASUS",
        "category": "laptop",
        "tier": "baja",
        "desc": "Un clásico de la resistencia militar. Destaca por su masiva batería en la gama económica y un procesador Ryzen que estira la autonomía al máximo en tareas comunes.",
        "priceUS": "$899 USD",
        "priceEU": "949 € (IVA incl.)",
        "specs": [
            {"label": "Procesador", "value": "AMD Ryzen 7 7735HS / 8845HS"},
            {"label": "Gráfica", "value": "NVIDIA GeForce RTX 4050 / 4060 Laptop"},
            {"label": "Batería", "value": "90 Wh (Líder en su segmento)"}
        ],
        "pros": ["Autonomía de batería sobresaliente.", "Certificación de resistencia militar.", "Fácil de expandir."],
        "contras": ["Pantalla con tiempo de respuesta algo lento.", "Diseño un poco robusto y rudo."]
    },
    "acer-nitro-v15": {
        "title": "Acer Nitro V 15",
        "brand": "Acer",
        "category": "laptop",
        "tier": "baja",
        "desc": "La opción ultra-económica más equilibrada. Un diseño más estilizado y delgado que los Nitro anteriores, ideal para estudiantes que quieren jugar a títulos competitivos.",
        "priceUS": "$749 USD",
        "priceEU": "799 € (IVA incl.)",
        "specs": [
            {"label": "Procesador", "value": "Intel Core i5-13420H"},
            {"label": "Gráfica", "value": "NVIDIA GeForce RTX 4050 Laptop (75W TGP)"},
            {"label": "Peso", "value": "2.1 kg (Bastante ligera)"}
        ],
        "pros": ["Precio de salida sumamente agresivo.", "Formato más compacto y transportable."],
        "contras": ["Límite de potencia gráfica (TGP) más bajo.", "Ventiladores ruidosos bajo estrés."]
    },

    # === GAMA MEDIA ===
    "hp-victus-16": {
        "title": "HP Victus 16 (Advanced)",
        "brand": "HP",
        "category": "laptop",
        "tier": "media",
        "desc": "La evolución de la gama media de HP con un diseño minimalista que no grita 'gamer'. Su rendimiento con la gráfica RTX 4060 exprime los 1080p y 1440p con DLSS.",
        "priceUS": "$1,199 USD",
        "priceEU": "1.299 € (IVA incl.)",
        "specs": [
            {"label": "Procesador", "value": "AMD Ryzen 7 8845HS"},
            {"label": "Gráfica", "value": "NVIDIA GeForce RTX 4060 Laptop (120W TGP)"},
            {"label": "Pantalla", "value": "16.1\" FHD IPS, 144Hz 100% sRGB"}
        ],
        "pros": ["Estética sobria apta para oficina/universidad.", "Pantalla con buena precisión de color."],
        "contras": ["La bisagra de la pantalla tiende a tambalearse.", "Chasis de plástico rígido."]
    },
    "rog-strix-g16": {
        "title": "ASUS ROG Strix G16",
        "brand": "ASUS",
        "category": "laptop",
        "tier": "media",
        "desc": "Pura estética eSports. Incorpora refrigeración de tres ventiladores y metal líquido sobre el procesador para asegurar tasas de refresco altísimas en juegos competitivos.",
        "priceUS": "$1,499 USD",
        "priceEU": "1.699 € (IVA incl.)",
        "specs": [
            {"label": "Procesador", "value": "Intel Core i7-14650HX"},
            {"label": "Gráfica", "value": "NVIDIA GeForce RTX 4060 / 4070 Laptop"},
            {"label": "Pantalla", "value": "16\" WUXGA (1200p) ROG Nebula, 165Hz"}
        ],
        "pros": ["Sistema de refrigeración masivo Tri-Fan.", "Iluminación RGB muy personalizable."],
        "contras": ["Chasis grueso y pesado.", "No cuenta con puerto Thunderbolt (en configs AMD)."]
    },
    "predator-helios-16": {
        "title": "Acer Predator Helios 16",
        "brand": "Acer",
        "category": "laptop",
        "tier": "media",
        "desc": "Una laptop de alto impacto físico y técnico. Su pantalla de formato 16:10 y resolución extendida la vuelven una opción excelente tanto para creadores de contenido como para jugadores duros.",
        "priceUS": "$1,599 USD",
        "priceEU": "1.749 € (IVA incl.)",
        "specs": [
            {"label": "Procesador", "value": "Intel Core i7-14700HX"},
            {"label": "Gráfica", "value": "NVIDIA GeForce RTX 4070 Laptop (140W TGP)"},
            {"label": "Pantalla", "value": "16\" WQXGA (2560x1600) IPS, 240Hz"}
        ],
        "pros": ["Pantalla de 240Hz espectacularmente rápida.", "TGP gráfico completamente desbloqueado."],
        "contras": ["Consumo energético muy elevado.", "Software de control un poco tosco."]
    },

    # === GAMA ALTA ===
    "zephyrus-g14": {
        "title": "ROG Zephyrus G14",
        "brand": "ASUS",
        "category": "laptop",
        "tier": "alta",
        "desc": "El equilibrio perfecto en la gama premium. Chasis unibody de aluminio CNC ultraligero y una deslumbrante pantalla OLED Nebula que ofrece negros perfectos y contraste infinito.",
        "priceUS": "$1,999 USD",
        "priceEU": "2.299 € (IVA incl.)",
        "specs": [
            {"label": "Procesador", "value": "AMD Ryzen 9 8945HS"},
            {"label": "Gráfica", "value": "NVIDIA GeForce RTX 4070 Laptop"},
            {"label": "Pantalla", "value": "14\" OLED 2.5K, 120Hz, G-Sync"}
        ],
        "pros": ["Diseño unibody de aluminio ultra-delgado.", "Pantalla OLED insuperable.", "Excelente portabilidad."],
        "contras": ["Memoria RAM soldada (no ampliable).", "Chasis caliente bajo juegos pesados."]
    },
    "legion-pro-7i": {
        "title": "Legion Pro 7i",
        "brand": "Lenovo",
        "category": "laptop",
        "tier": "alta",
        "desc": "La laptop definitiva para sustituir un ordenador de escritorio. Diseñada para exprimir al máximo los TGP más altos en tarjetas de grado entusiasta mediante cámara de vapor.",
        "priceUS": "$2,699 USD",
        "priceEU": "2.999 € (IVA incl.)",
        "specs": [
            {"label": "Procesador", "value": "Intel Core i9-14900HX"},
            {"label": "Gráfica", "value": "NVIDIA GeForce RTX 4080 Laptop (175W TGP)"},
            {"label": "Refrigeración", "value": "Cámara de vapor Coldfront 5.0 + Metal Líquido"}
        ],
        "pros": ["Rendimiento bruto masivo sin estrangulamiento.", "Calidad de construcción y teclado impecables."],
        "contras": ["El cargador es enorme.", "Batería de corta duración desconectada."]
    },
    "razer-blade-16": {
        "title": "Razer Blade 16",
        "brand": "Razer",
        "category": "laptop",
        "tier": "alta",
        "desc": "El tope de gama absoluto del lujo en PC. Chasis de aluminio anodizado con una pantalla revolucionaria Dual-Mode Mini-LED capaz de alternar resoluciones nativas por hardware.",
        "priceUS": "$2,999 USD",
        "priceEU": "3.399 € (IVA incl.)",
        "specs": [
            {"label": "Procesador", "value": "Intel Core i9 de Grado Entusiasta"},
            {"label": "Pantalla", "value": "16\" Dual-Mode Mini-LED (4K 120Hz / FHD+ 240Hz)"},
            {"label": "Gráfica", "value": "NVIDIA GeForce RTX 4090 Laptop"}
        ],
        "pros": ["Pantalla Mini-LED híbrida única.", "Estética limpia y acabados premium perfectos."],
        "contras": ["Precio extremadamente prohibitivo.", "El chasis de aluminio disipa el calor hacia el teclado."]
    }
}

def cargar_datos_existentes():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return HARDWARE_BASE.copy()

def guardar_datos(datos):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
    print(f"[ÉXITO] Archivo '{JSON_FILE}' actualizado con {len(datos)} equipos.")

def ejecutar_pipeline_diario():
    datos = cargar_datos_existentes()
    guardar_datos(datos)

if __name__ == "__main__":
    ejecutar_pipeline_diario()
