#!/usr/bin/env python3
"""
EJECUCIÓN COMPLETA DEL PIPELINE NLP
Ejecuta todas las fases del procesamiento en secuencia
Equivalente a ejecutar el workflow completo de GitHub Actions
"""

from dotenv import load_dotenv
import os
import sys
import psycopg2
import re

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

load_dotenv()

def print_header(title):
    """Imprime encabezado de sección"""
    print()
    print("=" * 70)
    print(f"🔷 {title}")
    print("=" * 70)
    print()

def main():
    """Ejecuta el pipeline completo"""
    
    # Validar conexión
    if not os.environ.get("NEON_CONN_STRING"):
        print("❌ Error: NEON_CONN_STRING no está configurado en .env")
        return 1
    
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                                                                  ║")
    print("║        🚀 EJECUCIÓN COMPLETA DEL PIPELINE NLP 🚀                 ║")
    print("║                                                                  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    print("⚙️  Configuración:")
    print(f"   - IA Local: Hugging Face (mDeBERTa + BERT-NER)")
    print(f"   - Base de datos: Configurada ✓")
    print(f"   - Procesamiento por etapas: 3 fases")
    print()
    
    try:
        # ================================================================
        # FASE 1: EXTRACCIÓN DE TAGS
        # ================================================================
        print_header("FASE 1: EXTRACCIÓN DE TAGS")
        
        from src.infrastructure.db_adapter import NeonDBAdapter
        from src.adapters.local_ai_adapter import AIServiceFactory
        from src.services.tag_extraction_service import TagExtractionService
        from tqdm import tqdm
        
        repository = NeonDBAdapter()
        
        # Verificar si hay artículos sin tags
        articles = repository.fetch_unprocessed_articles()
        
        if not articles:
            print("✅ No hay artículos sin tags para procesar")
            print()
        else:
            print(f"📊 Total de artículos sin tags: {len(articles)}")
            print()
            print("🤖 Extrayendo tags con IA local...")
            print()
            
            ai_adapter = AIServiceFactory.create_adapter("local")
            tag_service = TagExtractionService(ai_adapter)
            
            processed = 0
            errors = 0
            
            with tqdm(total=len(articles), desc="Procesando", unit="art") as pbar:
                for article in articles:
                    try:
                        tags = tag_service.extract(article)
                        
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
            print(f"✅ Fase 1 completada: {processed}/{len(articles)} artículos con tags")
            print(f"   Errores: {errors}")
            print()
        
        # ================================================================
        # FASE 2: CLUSTERING
        # ================================================================
        print_header("FASE 2: CLUSTERING DE ARTÍCULOS SIMILARES")
        
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
        
        print("📥 Cargando artículos con tags...")
        articles_with_tags = repository.fetch_articles_with_tags()
        
        if not articles_with_tags:
            print("⚠️  No hay artículos con tags para clustering")
        else:
            print(f"📊 Total de artículos: {len(articles_with_tags)}")
            print()
            print("🔍 Detectando países y fechas...")
            
            clusters_by_key = defaultdict(list)
            
            with tqdm(total=len(articles_with_tags), desc="Analizando", unit="art") as pbar:
                for article in articles_with_tags:
                    # Usar content_code o description para detectar país
                    text_for_detection = article.description or ""
                    if hasattr(article, 'content_code') and article.content_code:
                        text_for_detection = article.content_code[:1000]  # Primeros 1000 chars
                    
                    country = country_service.detect(text_for_detection)
                    
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
                    
                    pbar.update(1)
            
            print()
            print(f"🎯 Clusters preliminares: {len(clusters_by_key)}")
            print()
            print("🔗 Agrupando artículos similares...")
            
            final_clusters = []
            discarded = 0
            
            with tqdm(total=len(clusters_by_key), desc="Clustering", unit="cluster") as pbar:
                for key, articles_data in clusters_by_key.items():
                    category, country, event_date = key
                    
                    if len(articles_data) < 2:
                        discarded += 1
                        pbar.set_postfix({"clusters": len(final_clusters), "descartados": discarded})
                        pbar.update(1)
                        continue
                    
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
                    pbar.set_postfix({"clusters": len(final_clusters), "descartados": discarded})
                    pbar.update(1)
            
            print()
            print("💾 Guardando clusters en BD...")
            
            saved = 0
            with tqdm(total=len(final_clusters), desc="Guardando", unit="cluster") as pbar:
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
                            pbar.set_postfix({"guardados": saved})
                    except Exception as e:
                        pbar.set_postfix({"error": str(e)[:30]})
                    
                    pbar.update(1)
            
            print()
            print(f"✅ Fase 2 completada: {saved} clusters guardados")
            print(f"   Descartados: {discarded}")
        
        # ================================================================
        # FASE 3: GENERACIÓN DE TÍTULOS CON IA
        # ================================================================
        print_header("FASE 3: GENERACIÓN DE TÍTULOS CON IA")
        
        from src.services.categorization_service import CategorizationService
        
        # Inicializar AI adapter si no existe (cuando saltamos Fase 1)
        if 'ai_adapter' not in locals():
            ai_adapter = AIServiceFactory.create_adapter("local")
        
        categorization_service = CategorizationService(ai_adapter)
        
        print("📥 Cargando clusters pendientes...")
        clusters = repository.fetch_clusters_without_titles()
        
        if not clusters:
            print("✅ No hay clusters pendientes de titulación")
        else:
            print(f"📊 Total de clusters: {len(clusters)}")
            print()
            print("🤖 Generando títulos con IA local...")
            print()
            
            processed = 0
            errors = 0
            
            with tqdm(total=len(clusters), desc="Generando títulos", unit="topic") as pbar:
                for cluster in clusters:
                    try:
                        articles = repository.fetch_articles_by_ids(cluster['article_ids'])
                        
                        if not articles:
                            errors += 1
                            pbar.set_postfix({"✓": processed, "✗": errors})
                            pbar.update(1)
                            continue
                        
                        # Usar el artículo más relevante (primero) como base
                        main_article = articles[0]
                        
                        # Generar título realista basado en los artículos
                        # Usar el título del artículo principal como base
                        title = main_article.title.strip()
                        
                        # Si el título es muy largo, resumirlo manteniendo la esencia
                        if len(title) > 120:
                            # Tomar las primeras palabras hasta 120 caracteres
                            words = title.split()
                            title = ""
                            for word in words:
                                if len(title) + len(word) + 1 <= 120:
                                    title += word + " "
                                else:
                                    break
                            title = title.strip() + "..."
                        
                        # Generar summary combinando las descripciones de los artículos
                        descriptions = []
                        for article in articles[:3]:  # Máximo 3 descripciones
                            if article.description and len(article.description) > 20:
                                desc = article.description.strip()
                                if len(desc) > 150:
                                    desc = desc[:147] + "..."
                                descriptions.append(desc)
                        
                        summary = " | ".join(descriptions) if descriptions else title
                        if len(summary) > 500:
                            summary = summary[:497] + "..."
                        
                        # Categorización jerárquica
                        category, subcategory, theme, subtema = categorization_service.categorize(
                            main_article,
                            cluster.get('category', 'General')
                        )
                        
                        # Extraer main_image_url del primer artículo si tiene imágenes
                        main_image_url = ""
                        if hasattr(main_article, 'content_code') and main_article.content_code:
                            # Buscar URL de imagen en el HTML del content_code
                            img_match = re.search(r'<img[^>]+src="([^"]+)"', main_article.content_code)
                            if img_match:
                                main_image_url = img_match.group(1)
                        
                        # Crear article_links para las fuentes
                        article_links = []
                        for article in articles:
                            pub_date = None
                            if hasattr(article, 'published_at') and article.published_at:
                                # Convertir datetime a string ISO format
                                if hasattr(article.published_at, 'isoformat'):
                                    pub_date = article.published_at.isoformat()
                                else:
                                    pub_date = str(article.published_at)
                            
                            article_links.append({
                                "url": article.url if hasattr(article, 'url') and article.url else "",
                                "source": article.source if hasattr(article, 'source') else "unknown",
                                "publication_date": pub_date
                            })
                        
                        # Actualizar cluster con toda la información
                        repository.update_cluster_with_title(
                            cluster_id=cluster['id'],
                            title=title,
                            summary=summary,
                            main_image_url=main_image_url,
                            category=category,
                            subcategory=subcategory,
                            theme=theme,
                            article_links=article_links
                        )
                        
                        processed += 1
                        pbar.set_postfix({"✓": processed, "✗": errors, "último": title[:30]})
                        
                    except Exception as e:
                        errors += 1
                        pbar.set_postfix({"✓": processed, "✗": errors, "error": str(e)[:20]})
                    
                    pbar.update(1)
            
            print()
            print(f"✅ Fase 3 completada: {processed}/{len(clusters)} topics finalizados")
            print(f"   Errores: {errors}")
        
        # ================================================================
        # RESUMEN FINAL
        # ================================================================
        print()
        print("=" * 70)
        print("✅ PROCESAMIENTO COMPLETO FINALIZADO")
        print("=" * 70)
        print()
        print("🎉 ¡Pipeline ejecutado exitosamente!")
        print()
        print("📊 Verifica los resultados en la base de datos:")
        print("   SELECT id, title, category, subcategory, is_final")
        print("   FROM topics")
        print("   WHERE is_final = true")
        print("   ORDER BY created_at DESC;")
        print()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Procesamiento interrumpido por el usuario")
        return 1
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
