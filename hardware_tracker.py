# -*- coding: utf-8 -*-
"""
KazokuGaming - Robot Automatizado de Monitoreo de Hardware v1.1 (Año 2026)
"""

import json
import os
from datetime import datetime

JSON_FILE = "hardware.json"

# Base de datos ampliada con 9 equipos base y categorización explícita
HARDWARE_BASE = {
    "steam-deck": {
        "title": "Steam Deck OLED",
        "brand": "Valve",
        "category": "handheld",
        "desc": "La reina de la optimización portátil. Su pantalla OLED y la eficiencia de SteamOS la convierten en la opción más equilibrada del mercado.",
        "priceUS": "$549 USD",
        "priceEU": "569 € (IVA incl.)",
        "specs": [
            {"label": "Procesador / APU", "value": "AMD Sephiroth custom (6nm Zen 2 + RDNA 2)"},
            {"label": "Pantalla", "value": "7.4\" OLED HDR, 90Hz, 1,000 nits de brillo pico"},
            {"label": "Memoria RAM", "value": "16GB LPDDR5 a 6400 MT/s"},
            {"label": "Batería", "value": "50 Wh (Aprox. 3 a 12 horas de uso)"}
        ],
        "pros": ["Pantalla OLED HDR impecable.", "Eficiencia energética estelar.", "SteamOS es intuitivo."],
        "contras": ["Menos potencia bruta que sus competidores.", "Incompatibilidad con algunos Anti-Cheat."]
    },
    "rog-ally-x": {
        "title": "ROG Ally X",
        "brand": "ASUS",
        "category": "handheld",
        "desc": "Potencia bruta bajo Windows 11. Corrige los problemas de batería de su predecesora duplicando su capacidad a 80Wh y mejorando su ergonomía.",
        "priceUS": "$799 USD",
        "priceEU": "899 € (IVA incl.)",
        "specs": [
            {"label": "Procesador / APU", "value": "AMD Ryzen Z1 Extreme (Zen 4 + RDNA 3)"},
            {"label": "Pantalla", "value": "7\" IPS Full HD, 120Hz con VRR"},
            {"label": "Memoria RAM", "value": "24GB LPDDR5X a 7500 MT/s"},
            {"label": "Batería", "value": "80 Wh"}
        ],
        "pros": ["Batería masiva de 80Wh.", "24GB de RAM de alta velocidad.", "Pantalla con VRR muy fluida."],
        "contras": ["Windows 11 no está adaptado al 100% a portátiles.", "Panel IPS en lugar de OLED."]
    },
    "legion-go": {
        "title": "Lenovo Legion Go",
        "brand": "Lenovo",
        "category": "handheld",
        "desc": "La experiencia híbrida definitiva. Su gigantesca pantalla táctil de 8.8 pulgadas y mandos desmontables con 'Modo FPS' la convierten en una bestia multimedia.",
        "priceUS": "$699 USD",
        "priceEU": "799 € (IVA incl.)",
        "specs": [
            {"label": "Procesador / APU", "value": "AMD Ryzen Z1 Extreme"},
            {"label": "Pantalla", "value": "8.8\" QHD+ (1600p) IPS, 144Hz"},
            {"label": "Innovación", "value": "Mandos desmontables TrueStrike"}
        ],
        "pros": ["Pantalla gigante de alta resolución.", "Mandos modulares con modo ratón."],
        "contras": ["Dispositivo pesado y voluminoso.", "La batería se drena rápido a 1600p."]
    },
    "ayaneo-3": {
        "title": "AYANEO 3",
        "brand": "AYANEO",
        "category": "handheld",
        "desc": "El titán de las consolas boutique chinas. Ofrece acabados ultra premium, joysticks magnéticos de efecto Hall y una de las pantallas OLED más brillantes del sector.",
        "priceUS": "$999 USD",
        "priceEU": "1.049 € (Importación)",
        "specs": [
            {"label": "Procesador", "value": "AMD Ryzen 7 de última generación"},
            {"label": "Pantalla", "value": "7\" OLED Premium calibrado sRGB"},
            {"label": "Controles", "value": "Gatillos y Joysticks de Efecto Hall"}
        ],
        "pros": ["Calidad de construcción premium.", "Sin desgaste en joysticks (cero drift)."],
        "contras": ["Precio elevado de gama entusiasta.", "Soporte postventa internacional complejo."]
    },
    "gpd-win-mini": {
        "title": "GPD Win Mini (2026)",
        "brand": "GPD",
        "category": "handheld",
        "desc": "Diseño ultra-compacto de origen chino con formato de concha (clamshell) y teclado físico completo integrado. Auténtica potencia de PC en tu bolsillo.",
        "priceUS": "$899 USD",
        "priceEU": "949 € (Importación)",
        "specs": [
            {"label": "Procesador / APU", "value": "AMD Ryzen 7 Premium con RDNA 3.5"},
            {"label": "Diseño", "value": "Formato Concha con teclado QWERTY"},
            {"label": "Conexión", "value": "Puerto OCuLink nativo para eGPU"}
        ],
        "pros": ["Ultra portátil, cabe en un bolsillo.", "Teclado físico muy práctico para chats y comandos."],
        "contras": ["Ergonomía algo sacrificada.", "Se calienta debido a su tamaño compacto."]
    },
    "zephyrus-g14": {
        "title": "ROG Zephyrus G14",
        "brand": "ASUS",
        "category": "laptop",
        "desc": "El equilibrio perfecto en laptops gaming. Chasis unibody de aluminio CNC ultraligero y pantalla OLED Nebula que ofrece negros perfectos.",
        "priceUS": "$1,999 USD",
        "priceEU": "2.299 € (IVA incl.)",
        "specs": [
            {"label": "Procesador", "value": "AMD Ryzen 9 de alta eficiencia"},
            {"label": "Gráfica", "value": "NVIDIA GeForce RTX 4070 Laptop"},
            {"label": "Pantalla", "value": "14\" OLED 2.5K, 120Hz, G-Sync"}
        ],
        "pros": ["Diseño premium, delgado y sobrio.", "Pantalla OLED espectacular.", "Gran autonomía portátil."],
        "contras": ["Memoria RAM soldada en placa.", "Ventiladores algo ruidosos bajo carga máxima."]
    },
    "legion-pro-7i": {
        "title": "Legion Pro 7i",
        "brand": "Lenovo",
        "category": "laptop",
        "desc": "La laptop definitiva para sustituir un ordenador de escritorio. Diseñada para exprimir al máximo el TGP de las tarjetas gráficas RTX sin estrangulamiento térmico.",
        "priceUS": "$2,699 USD",
        "priceEU": "2.999 € (IVA incl.)",
        "specs": [
            {"label": "Procesador", "value": "Intel Core i9 Grado Entusiasta"},
            {"label": "Gráfica", "value": "NVIDIA GeForce RTX 4080 (175W TGP)"},
            {"label": "Refrigeración", "value": "Cámara de vapor Coldfront 5.0"}
        ],
        "pros": ["Rendimiento gráfico desatado.", "Excelente disipación térmica con metal líquido."],
        "contras": ["Cargador de corriente enorme y pesado.", "Poca duración de batería desenchufada."]
    },
    "razer-blade-16": {
        "title": "Razer Blade 16 (2026)",
        "brand": "Razer",
        "category": "laptop",
        "desc": "El 'MacBook' de los jugadores. Chasis de aluminio anodizado impecable con la primera pantalla del mundo Dual-Mode Mini-LED capaz de alternar resoluciones nativas.",
        "priceUS": "$2,999 USD",
        "priceEU": "3.399 € (IVA incl.)",
        "specs": [
            {"label": "Procesador", "value": "Intel Core i9 de última generación"},
            {"label": "Pantalla", "value": "16\" Dual-Mode Mini-LED (4K 120Hz / FHD+ 240Hz)"},
            {"label": "Gráfica", "value": "NVIDIA GeForce RTX 4090 Laptop"}
        ],
        "pros": ["Pantalla Mini-LED revolucionaria.", "Estética y acabados de lujo insuperables."],
        "contras": ["Precio extremadamente elevado.", "El chasis se calienta notablemente al jugar."]
    },
    "ps5-pro": {
        "title": "PlayStation 5 Pro",
        "brand": "Sony",
        "category": "console",
        "desc": "Consola de sobremesa diseñada para jugar a 60FPS estables manteniendo modos de alta fidelidad visual gracias al reescalado por inteligencia artificial PSSR.",
        "priceUS": "$699 USD",
        "priceEU": "799 € (Precio Oficial)",
        "specs": [
            {"label": "Tecnología Clave", "value": "PSSR (AI Upscaling) & Ray Tracing Avanzado"},
            {"label": "Almacenamiento", "value": "2TB Custom NVMe SSD"}
        ],
        "pros": ["Rendimiento impecable a 60 FPS.", "El reescalado por IA de Sony es limpio y nítido."],
        "contras": ["Precio elevado.", "No incluye lector de discos físico de serie."]
    },
    "xbox-series-x": {
        "title": "Xbox Series X (Digital)",
        "brand": "Microsoft",
        "category": "console",
        "desc": "El monolito de rendimiento de Microsoft optimizado para un entorno puramente digital y suscripciones del ecosistema Game Pass Ultimate.",
        "priceUS": "$449 USD",
        "priceEU": "499 € (IVA incl.)",
        "specs": [
            {"label": "Potencia", "value": "12 Teraflops RDNA 2"},
            {"label": "Funciones", "value": "Quick Resume & Smart Delivery"}
        ],
        "pros": ["Consola extremadamente silenciosa.", "Quick Resume es una maravilla de software."],
        "contras": ["Dependencia absoluta de la tienda digital."]
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
    # Aquí puedes añadir tus funciones de scraping en vivo si lo deseas
    guardar_datos(datos)

if __name__ == "__main__":
    ejecutar_pipeline_diario()
