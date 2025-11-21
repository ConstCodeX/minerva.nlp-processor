#!/usr/bin/env python3
"""
PASO 2: Agrupar artículos similares en clusters (pre-topics)
- Lee artículos con tags
- Calcula similitud entre artículos
- Agrupa por tags compartidos + país + fecha
- Valida mínimo 2 fuentes diferentes
- Guarda clusters en BD (sin título final aún)
- Muestra progreso en CLI
"""

from dotenv import load_dotenv
from src.infrastructure.db_adapter import NeonDBAdapter
from src.services.country_detection_service import CountryDetectionService
from collections import defaultdict
from datetime import date, datetime
import os
from tqdm import tqdm

load_dotenv()

def calculate_tag_similarity(tags1: list, tags2: list) -> float:
    """Calcula similitud entre dos conjuntos de tags (Jaccard)"""
    set1 = set(tags1)
    set2 = set(tags2)
    
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0

def cluster_articles():
    """Agrupa artículos similares en clusters"""
    
    if not os.environ.get("NEON_CONN_STRING"):
        print("❌ Error: NEON_CONN_STRING no configurado")
        return
    
    print("=" * 70)
    print("🔗 PASO 2: CLUSTERING DE ARTÍCULOS")
    print("=" * 70)
    print()
    
    # Inicializar servicios
    print("🔧 Inicializando servicios...")
    repository = NeonDBAdapter()
    country_service = CountryDetectionService()
    
    # Obtener artículos con tags (ya procesados en paso 1)
    print("📥 Cargando artículos con tags...")
    articles = repository.fetch_articles_with_tags()
    
    if not articles:
        print("❌ No hay artículos con tags")
        print("📌 Ejecuta primero: python3 main_step1_tags.py")
        return
    
    print(f"📊 Total de artículos: {len(articles)}")
    print()
    print("🔍 Detectando países y fechas...")
    
    # Estructuras para clustering
    # {(category, country, date): [article_data]}
    clusters_by_key = defaultdict(list)
    
    # Enriquecer artículos con país y fecha
    with tqdm(total=len(articles), desc="Analizando", unit="art") as pbar:
        for article in articles:
            # Detectar país
            country = country_service.detect(article.content or article.description or "")
            
            # Extraer fecha
            event_date = None
            if hasattr(article, 'published_at') and article.published_at:
                if isinstance(article.published_at, datetime):
                    event_date = article.published_at.date()
                elif isinstance(article.published_at, date):
                    event_date = article.published_at
            
            if not event_date:
                event_date = date.today()
            
            # Obtener categoría base (si existe)
            category = getattr(article, 'category', 'General')
            
            # Clave de agrupación
            key = (category, country, str(event_date))
            
            # Agregar a cluster
            clusters_by_key[key].append({
                'article': article,
                'tags': getattr(article, 'tags', []),
                'source': article.source_name
            })
            
            pbar.update(1)
    
    print()
    print(f"🎯 Clusters preliminares: {len(clusters_by_key)}")
    print()
    print("🔗 Agrupando artículos similares...")
    
    # Ahora agrupar por similitud de tags dentro de cada cluster
    final_clusters = []
    discarded = 0
    
    with tqdm(total=len(clusters_by_key), desc="Clustering", unit="cluster") as pbar:
        for key, articles_data in clusters_by_key.items():
            category, country, event_date = key
            
            # Si hay menos de 2 artículos, descartar
            if len(articles_data) < 2:
                discarded += 1
                pbar.set_postfix({"clusters": len(final_clusters), "descartados": discarded})
                pbar.update(1)
                continue
            
            # Agrupar por similitud de tags
            temp_clusters = []
            used = set()
            
            for i, data1 in enumerate(articles_data):
                if i in used:
                    continue
                
                cluster_group = [data1]
                used.add(i)
                
                # Buscar artículos similares
                for j, data2 in enumerate(articles_data[i+1:], start=i+1):
                    if j in used:
                        continue
                    
                    similarity = calculate_tag_similarity(data1['tags'], data2['tags'])
                    
                    # Si similitud > 0.3, agrupar
                    if similarity >= 0.3:
                        cluster_group.append(data2)
                        used.add(j)
                
                # Validar: mínimo 2 artículos y 2 fuentes diferentes
                if len(cluster_group) >= 2:
                    sources = set(d['source'] for d in cluster_group)
                    if len(sources) >= 2:
                        # Extraer tags comunes
                        all_tags = []
                        for d in cluster_group:
                            all_tags.extend(d['tags'])
                        
                        # Contar frecuencia de tags
                        tag_freq = defaultdict(int)
                        for tag in all_tags:
                            tag_freq[tag] += 1
                        
                        # Tags que aparecen en al menos 2 artículos
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
    
    # Guardar clusters (pre-topics sin título final)
    saved = 0
    with tqdm(total=len(final_clusters), desc="Guardando", unit="cluster") as pbar:
        for cluster in final_clusters:
            try:
                # Crear título temporal basado en tags principales
                temp_title = f"Cluster: {', '.join(cluster['tags'][:3])}"
                
                # Guardar en BD como pre-topic
                article_ids = [a.id for a in cluster['articles']]
                repository.save_cluster(
                    temp_title=temp_title,
                    category=cluster['category'],
                    country=cluster['country'],
                    event_date=cluster['event_date'],
                    tags=cluster['tags'],
                    article_ids=article_ids
                )
                saved += 1
                pbar.set_postfix({"guardados": saved})
            except Exception as e:
                pbar.set_postfix({"error": str(e)[:30]})
            
            pbar.update(1)
    
    print()
    print("=" * 70)
    print("✅ PASO 2 COMPLETADO")
    print("=" * 70)
    print(f"  ✓ Clusters creados: {len(final_clusters)}")
    print(f"  ✓ Guardados en BD: {saved}")
    print(f"  ✗ Descartados: {discarded}")
    print()
    print("📌 Próximo paso: python3 main_step3_titles.py")
    print()

if __name__ == "__main__":
    cluster_articles()
