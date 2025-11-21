#!/usr/bin/env python3
"""
PASO 1: Extraer y guardar tags para cada artículo
- Lee artículos sin procesar
- Extrae tags usando IA local (NER)
- Guarda tags en la BD
- Muestra progreso en CLI
"""

from dotenv import load_dotenv
from src.infrastructure.db_adapter import NeonDBAdapter
from src.adapters.local_ai_adapter import AIServiceFactory
from src.services.tag_extraction_service import TagExtractionService
import os
from tqdm import tqdm

load_dotenv()

def extract_and_save_tags():
    """Extrae tags de artículos no procesados y los guarda en BD"""
    
    if not os.environ.get("NEON_CONN_STRING"):
        print("❌ Error: NEON_CONN_STRING no configurado")
        return
    
    print("=" * 70)
    print("📋 PASO 1: EXTRACCIÓN DE TAGS")
    print("=" * 70)
    print()
    
    # Inicializar servicios
    print("🔧 Inicializando servicios...")
    repository = NeonDBAdapter()
    ai_adapter = AIServiceFactory.create_adapter("local")
    tag_service = TagExtractionService(ai_adapter)
    
    # Obtener artículos sin procesar
    print("📥 Cargando artículos sin procesar...")
    articles = repository.fetch_unprocessed_articles()
    
    if not articles:
        print("✅ No hay artículos pendientes de procesar")
        return
    
    print(f"📊 Total de artículos: {len(articles)}")
    print()
    print("🤖 Extrayendo tags con IA local...")
    print()
    
    processed = 0
    errors = 0
    
    # Procesar con barra de progreso
    with tqdm(total=len(articles), desc="Procesando", unit="art") as pbar:
        for article in articles:
            try:
                # Extraer tags
                tags = tag_service.extract(article)
                
                # Guardar en BD (actualizar el artículo con tags)
                if tags:
                    repository.update_article_tags(article.id, tags)
                    processed += 1
                    pbar.set_postfix({"tags": len(tags), "✓": processed, "✗": errors})
                else:
                    pbar.set_postfix({"tags": 0, "✓": processed, "✗": errors})
                
            except Exception as e:
                errors += 1
                pbar.set_postfix({"error": str(e)[:30], "✓": processed, "✗": errors})
            
            pbar.update(1)
    
    print()
    print("=" * 70)
    print("✅ PASO 1 COMPLETADO")
    print("=" * 70)
    print(f"  ✓ Artículos procesados: {processed}/{len(articles)}")
    print(f"  ✗ Errores: {errors}")
    print()
    print("📌 Próximo paso: python3 main_step2_clustering.py")
    print()

if __name__ == "__main__":
    extract_and_save_tags()
