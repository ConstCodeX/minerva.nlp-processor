import os
from dotenv import load_dotenv

# Carga las variables de entorno del archivo .env
load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# Configuración de IA Local con Ollama
# Modelos recomendados (ordenados por velocidad/calidad):
# - qwen2.5:7b (el más rápido, excelente para español)
# - llama3.1:8b (muy bueno, balanceado)
# - mistral:7b (bueno para categorización)
AI_MODEL: str = os.getenv("AI_MODEL", "qwen2.5:7b")
