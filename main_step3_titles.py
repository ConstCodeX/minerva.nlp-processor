#!/usr/bin/env python3
"""
PASO 3: Generar títulos finales para topics con IA
- Lee clusters (pre-topics) de la BD
- Analiza artículos de cada cluster
- Genera título único y representativo con IA
- Extrae categorización jerárquica (category → subcategory → theme → subtema)
- Actualiza topics en BD con títulos finales
- Muestra progreso en CLI
"""

from dotenv import load_dotenv
from src.infrastructure.db_adapter import NeonDBAdapter
from src.adapters.local_ai_adapter import AIServiceFactory
from src.services.categorization_service import CategorizationService
import os
from tqdm import tqdm

load_dotenv()

def generate_title_with_ai(articles: list, tags: list, ai_adapter) -> str:
    """
    Genera un título único y representativo para el topic usando IA.
    
    Analiza:
    - Títulos de artículos del cluster
    - Tags principales
    - Contexto común
    
    Retorna: Título conciso y descriptivo
    """
    # Recopilar información del cluster
    titles = [a.title for a in articles if a.title]
    
    if not titles:
        return f"Noticias sobre {', '.join(tags[:2])}"
    
    # Preparar texto para análisis
    # Tomar los 3 primeros títulos más largos (más informativos)
    titles_sorted = sorted(titles, key=len, reverse=True)[:3]
    combined_text = " | ".join(titles_sorted)
    
    # Usar IA para extraer el tema principal
    # Usamos categorización para identificar el tema central
    try:
        # Simular un artículo con el texto combinado
        class TempArticle:
            def __init__(self, title, description):
                self.title = title
                self.description = description
                self.content = description
        
        temp_article = TempArticle(
            title=titles[0],
            description=combined_text
        )
        
        # Extraer tema usando categorización
        categorization_service = CategorizationService(ai_adapter)
        _, _, theme, subtema = categorization_service.categorize(temp_article, "General")
        
        # Generar título basado en theme y subtema
        if theme and subtema and theme != "Sin clasificar":
            # Combinar theme y subtema para crear título significativo
            title = f"{theme}: {subtema}"
            return title[:200]  # Límite de caracteres
        
    except Exception as e:
        print(f"⚠️  Error generando título con IA: {e}")
    
    # Fallback: usar el título más común o el primero
    return titles[0][:200]

def generate_titles():
    """Genera títulos finales para clusters con IA"""
    
    if not os.environ.get("NEON_CONN_STRING"):
        print("❌ Error: NEON_CONN_STRING no configurado")
        return
    
    print("=" * 70)
    print("✨ PASO 3: GENERACIÓN DE TÍTULOS CON IA")
    print("=" * 70)
    print()
    
    # Inicializar servicios
    print("🔧 Inicializando servicios...")
    repository = NeonDBAdapter()
    ai_adapter = AIServiceFactory.create_adapter("local")
    categorization_service = CategorizationService(ai_adapter)
    
    # Obtener clusters sin título final
    print("📥 Cargando clusters pendientes...")
    clusters = repository.fetch_clusters_without_titles()
    
    if not clusters:
        print("✅ No hay clusters pendientes")
        print("📌 Todos los topics tienen títulos finales")
        return
    
    print(f"📊 Total de clusters: {len(clusters)}")
    print()
    print("🤖 Generando títulos con IA local...")
    print()
    
    processed = 0
    errors = 0
    
    # Procesar con barra de progreso
    with tqdm(total=len(clusters), desc="Generando títulos", unit="topic") as pbar:
        for cluster in clusters:
            try:
                # Obtener artículos del cluster
                articles = repository.fetch_articles_by_ids(cluster['article_ids'])
                
                if not articles:
                    errors += 1
                    pbar.set_postfix({"✓": processed, "✗": errors})
                    pbar.update(1)
                    continue
                
                # Generar título con IA
                title = generate_title_with_ai(
                    articles=articles,
                    tags=cluster['tags'],
                    ai_adapter=ai_adapter
                )
                
                # Obtener categorización jerárquica del primer artículo (representativo)
                first_article = articles[0]
                category, subcategory, theme, subtema = categorization_service.categorize(
                    first_article,
                    cluster.get('category', 'General')
                )
                
                # Actualizar topic en BD
                repository.update_cluster_with_title(
                    cluster_id=cluster['id'],
                    title=title,
                    category=category,
                    subcategory=subcategory,
                    theme=theme,
                    subtema=subtema
                )
                
                processed += 1
                pbar.set_postfix({"✓": processed, "✗": errors, "último": title[:30]})
                
            except Exception as e:
                errors += 1
                pbar.set_postfix({"✓": processed, "✗": errors, "error": str(e)[:20]})
            
            pbar.update(1)
    
    print()
    print("=" * 70)
    print("✅ PASO 3 COMPLETADO")
    print("=" * 70)
    print(f"  ✓ Topics finalizados: {processed}/{len(clusters)}")
    print(f"  ✗ Errores: {errors}")
    print()
    print("🎉 ¡Procesamiento completo!")
    print("📌 Verifica los topics en la base de datos")
    print()

if __name__ == "__main__":
    generate_titles()
