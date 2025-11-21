#!/usr/bin/env python3
"""
PRUEBA COMPLETA DEL SISTEMA DE PROCESAMIENTO POR ETAPAS
Ejecuta todo el pipeline de forma automática con límites para pruebas rápidas
"""

from dotenv import load_dotenv
import os
import sys

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

load_dotenv()

def test_complete_pipeline():
    """Ejecuta el pipeline completo con límite de artículos para pruebas"""
    
    conn_string = os.environ.get("NEON_CONN_STRING")
    if not conn_string:
        print("❌ Error: NEON_CONN_STRING no configurado en .env")
        return False
    
    # Validar formato de conexión
    if not conn_string.startswith("postgresql://"):
        print("❌ Error: NEON_CONN_STRING debe comenzar con postgresql://")
        print(f"   Formato actual: {conn_string[:20]}...")
        return False
    
    print("=" * 70)
    print("🧪 PRUEBA COMPLETA DEL PIPELINE NLP")
    print("=" * 70)
    print()
    
    # ==================================================================
    # FASE 1: EXTRACCIÓN DE TAGS (LÍMITE: 50 artículos para prueba)
    # ==================================================================
    print("━" * 70)
    print("📋 FASE 1: EXTRACCIÓN DE TAGS (Límite: 50 artículos)")
    print("━" * 70)
    print()
    
    from src.infrastructure.db_adapter import NeonDBAdapter
    from src.adapters.local_ai_adapter import AIServiceFactory
    from src.services.tag_extraction_service import TagExtractionService
    
    repository = NeonDBAdapter()
    ai_adapter = AIServiceFactory.create_adapter("local")
    tag_service = TagExtractionService(ai_adapter)
    
    # Obtener artículos sin procesar (límite para prueba)
    articles = repository.fetch_unprocessed_articles()
    
    if not articles:
        print("✅ No hay artículos pendientes")
    else:
        # Limitar a 50 para prueba rápida
        test_limit = min(50, len(articles))
        articles = articles[:test_limit]
        
        print(f"📊 Procesando {len(articles)} artículos (muestra de prueba)")
        print()
        
        processed = 0
        errors = 0
        
        for i, article in enumerate(articles, 1):
            try:
                tags = tag_service.extract(article)
                
                if tags:
                    repository.update_article_tags(article.id, tags)
                    processed += 1
                    print(f"  [{i}/{len(articles)}] ✓ {article.title[:60]}... ({len(tags)} tags)")
                else:
                    print(f"  [{i}/{len(articles)}] ○ {article.title[:60]}... (sin tags)")
                
            except Exception as e:
                errors += 1
                print(f"  [{i}/{len(articles)}] ✗ Error: {str(e)[:50]}")
        
        print()
        print(f"✓ Fase 1 completada: {processed}/{len(articles)} artículos con tags")
        print()
    
    # ==================================================================
    # FASE 2: CLUSTERING
    # ==================================================================
    print("━" * 70)
    print("🔗 FASE 2: CLUSTERING DE ARTÍCULOS")
    print("━" * 70)
    print()
    
    from src.services.country_detection_service import CountryDetectionService
    from collections import defaultdict
    from datetime import date, datetime
    
    def calculate_tag_similarity(tags1, tags2):
        set1, set2 = set(tags1), set(tags2)
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    country_service = CountryDetectionService()
    
    # Obtener artículos con tags
    articles_with_tags = repository.fetch_articles_with_tags()
    
    if not articles_with_tags:
        print("⚠️  No hay artículos con tags para clustering")
    else:
        print(f"📊 Analizando {len(articles_with_tags)} artículos con tags")
        print()
        
        # Agrupar por (category, country, date)
        clusters_by_key = defaultdict(list)
        
        for article in articles_with_tags:
            country = country_service.detect(article.content or article.description or "")
            
            event_date = None
            if hasattr(article, 'published_at') and article.published_at:
                if isinstance(article.published_at, datetime):
                    event_date = article.published_at.date()
                elif isinstance(article.published_at, date):
                    event_date = article.published_at
            
            if not event_date:
                event_date = date.today()
            
            category = getattr(article, 'category', 'General')
            key = (category, country, str(event_date))
            
            clusters_by_key[key].append({
                'article': article,
                'tags': getattr(article, 'tags', []),
                'source': getattr(article, 'source', 'unknown')
            })
        
        print(f"🎯 Grupos preliminares: {len(clusters_by_key)}")
        print()
        
        # Clustering por similitud de tags
        final_clusters = []
        discarded = 0
        
        for key, articles_data in clusters_by_key.items():
            category, country, event_date = key
            
            if len(articles_data) < 2:
                discarded += 1
                continue
            
            # Agrupar por similitud
            temp_clusters = []
            used = set()
            
            for i, data1 in enumerate(articles_data):
                if i in used:
                    continue
                
                cluster_group = [data1]
                used.add(i)
                
                for j, data2 in enumerate(articles_data[i+1:], start=i+1):
                    if j in used:
                        continue
                    
                    similarity = calculate_tag_similarity(data1['tags'], data2['tags'])
                    
                    if similarity >= 0.3:
                        cluster_group.append(data2)
                        used.add(j)
                
                # Validar
                if len(cluster_group) >= 2:
                    sources = set(d['source'] for d in cluster_group)
                    if len(sources) >= 2:
                        all_tags = []
                        for d in cluster_group:
                            all_tags.extend(d['tags'])
                        
                        tag_freq = defaultdict(int)
                        for tag in all_tags:
                            tag_freq[tag] += 1
                        
                        common_tags = [tag for tag, freq in tag_freq.items() if freq >= 2]
                        
                        if common_tags:
                            temp_clusters.append({
                                'category': category,
                                'country': country,
                                'event_date': event_date,
                                'tags': common_tags,
                                'articles': [d['article'] for d in cluster_group],
                                'sources': list(sources)
                            })
                else:
                    discarded += 1
            
            final_clusters.extend(temp_clusters)
        
        print(f"✓ Clusters creados: {len(final_clusters)}")
        print(f"✗ Descartados: {discarded}")
        print()
        
        # Guardar clusters
        saved = 0
        for cluster in final_clusters:
            try:
                temp_title = f"Cluster: {', '.join(cluster['tags'][:3])}"
                article_ids = [a.id for a in cluster['articles']]
                
                cluster_id = repository.save_cluster(
                    temp_title=temp_title,
                    category=cluster['category'],
                    country=cluster['country'],
                    event_date=cluster['event_date'],
                    tags=cluster['tags'],
                    article_ids=article_ids
                )
                
                if cluster_id:
                    saved += 1
                    print(f"  ✓ Cluster #{cluster_id}: {temp_title[:60]} ({len(article_ids)} arts)")
                
            except Exception as e:
                print(f"  ✗ Error guardando cluster: {str(e)[:50]}")
        
        print()
        print(f"✓ Fase 2 completada: {saved} clusters guardados")
        print()
    
    # ==================================================================
    # FASE 3: GENERACIÓN DE TÍTULOS CON IA
    # ==================================================================
    print("━" * 70)
    print("✨ FASE 3: GENERACIÓN DE TÍTULOS CON IA")
    print("━" * 70)
    print()
    
    from src.services.categorization_service import CategorizationService
    
    categorization_service = CategorizationService(ai_adapter)
    
    # Obtener clusters sin título final
    clusters = repository.fetch_clusters_without_titles()
    
    if not clusters:
        print("✅ No hay clusters pendientes de titulación")
    else:
        print(f"📊 Generando títulos para {len(clusters)} clusters")
        print()
        
        processed = 0
        errors = 0
        
        for cluster in clusters:
            try:
                articles = repository.fetch_articles_by_ids(cluster['article_ids'])
                
                if not articles:
                    errors += 1
                    continue
                
                # Generar título basado en el primer artículo
                first_article = articles[0]
                
                # Obtener categorización jerárquica
                category, subcategory, theme, subtema = categorization_service.categorize(
                    first_article,
                    cluster.get('category', 'General')
                )
                
                # Título basado en theme y subtema
                if theme and subtema and theme != "Sin clasificar":
                    title = f"{theme}: {subtema}"[:200]
                else:
                    title = first_article.title[:200]
                
                # Actualizar topic
                repository.update_cluster_with_title(
                    cluster_id=cluster['id'],
                    title=title,
                    category=category,
                    subcategory=subcategory,
                    theme=theme,
                    subtema=subtema
                )
                
                processed += 1
                print(f"  [{processed}/{len(clusters)}] ✓ {title[:60]}")
                
            except Exception as e:
                errors += 1
                print(f"  [{processed+errors}/{len(clusters)}] ✗ Error: {str(e)[:50]}")
        
        print()
        print(f"✓ Fase 3 completada: {processed}/{len(clusters)} topics finalizados")
        print()
    
    # ==================================================================
    # RESUMEN FINAL
    # ==================================================================
    print("=" * 70)
    print("✅ PRUEBA COMPLETA FINALIZADA")
    print("=" * 70)
    print()
    print("📊 Verifica los resultados en la base de datos:")
    print("   SELECT id, title, category, subcategory, is_final")
    print("   FROM topics")
    print("   WHERE is_final = true")
    print("   ORDER BY created_at DESC;")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = test_complete_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
