# main.py
from dotenv import load_dotenv
from src.core.processing_service import NewsProcessingService
from src.infrastructure.db_adapter import NeonDBAdapter
from src.infrastructure.nlp_adapter import NLPAdapter
import os

# Carga la cadena de conexión de Neon.tech
load_dotenv() 
# Asegúrate de que la variable de entorno NEON_CONN_STRING esté definida
# (host=... user=... password=... dbname=... sslmode=require)

def run_processor():
    """Orquesta la ejecución del microservicio."""
    if not os.environ.get("NEON_CONN_STRING"):
        print("Error: La variable de entorno NEON_CONN_STRING no está configurada.")
        return

    # Inicializa Adaptadores
    repository = NeonDBAdapter()
    nlp_service = NLPAdapter()

    # Inicializa el Servicio de Dominio con los Puertos implementados (Inyección de Dependencias)
    processor = NewsProcessingService(
        repository=repository, 
        nlp_service=nlp_service
    )

    print("Iniciando procesamiento de artículos crudos...")
    processor.process_and_save_topics()
    print("Procesamiento completado.")

if __name__ == "__main__":
    run_processor()