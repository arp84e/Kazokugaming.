import json
import os

print("--- EJECUTANDO SCRIPT DE PRUEBA ---")

# Vamos a forzar un dato para ver si realmente se escribe en el archivo
datos_prueba = {
    "juegos": [
        {
            "id": "prueba-1",
            "titulo": "PRUEBA DE ESCRITURA EXITOSA",
            "fecha": "Hoy",
            "plataformas": "PC",
            "calificacion": "10",
            "motor_grafico": "Debug Engine",
            "tecnologias": "Ninguna",
            "rendimiento": "60 FPS",
            "sinopsis": "Si ves esto, el bot escribe correctamente.",
            "analisis_detallado": "<p>Prueba exitosa.</p>",
            "requisitos": {"minimos": ["Ninguno"], "recomendados": ["Ninguno"]},
            "imagen": "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=400"
        }
    ]
}

try:
    with open('telemetria.json', 'w', encoding='utf-8') as f:
        json.dump(datos_prueba, f, ensure_ascii=False, indent=2)
    print("✅ Archivo escrito correctamente.")
except Exception as e:
    print(f"❌ ERROR AL ESCRIBIR: {e}")
