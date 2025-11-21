# src/infrastructure/db_adapter.py
import psycopg2
import os
import json
from typing import List
from src.core.ports import ArticleRepository
from src.core.domain import Article, TopicData

class NeonDBAdapter(ArticleRepository):
    def __init__(self):
        # Cadena de conexión de Neon.tech
        self.conn_string = os.environ.get("NEON_CONN_STRING")

    def fetch_unprocessed_articles(self) -> List[Article]:
        """Obtiene artículos sin topic_id asignado con su categoría, fuente y fecha."""
        conn = psycopg2.connect(self.conn_string)
        cursor = conn.cursor()
        
        # Obtiene TODOS los artículos sin procesar (sin topic_id) con categoría, source y publication_date
        cursor.execute("""
            SELECT id, title, description, url, content_code, category, source, publication_date 
            FROM articles 
            WHERE topic_id IS NULL 
            ORDER BY publication_date DESC;
        """)
        
        articles = [
            Article(
                id=row[0], 
                title=row[1], 
                description=row[2], 
                content_code=row[3],
                url=row[4],
                category=row[5] or "General",  # Si no tiene categoría, asignar General
                source=row[6],  # Fuente del artículo (el comercio, la república, etc)
                published_at=row[7]  # Fecha de publicación
            ) 
            for row in cursor.fetchall()
        ]
        cursor.close()
        conn.close()
        return articles

    def save_new_topic(self, topic: TopicData, article_ids: List[int], article_relevance_scores: dict = None):
        """
        Guarda el tópico con categorización jerárquica y actualiza los artículos en una transacción.
        
        Args:
            topic: Datos del topic a guardar
            article_ids: Lista de IDs de artículos
            article_relevance_scores: Diccionario {article_id: relevance_score} con porcentajes de relevancia
        """
        conn = psycopg2.connect(self.conn_string)
        conn.autocommit = False # Inicia la transacción
        cursor = conn.cursor()
        
        try:
            # 1. Obtener datos completos de los artículos (incluyendo imágenes)
            cursor.execute("""
                SELECT a.id, a.url, a.source, a.publication_date, a.title,
                       (SELECT i.url FROM images i WHERE i.article_id = a.id ORDER BY i.width DESC LIMIT 1) as image_url
                FROM articles a
                WHERE a.id = ANY(%s)
                ORDER BY a.publication_date DESC;
            """, (article_ids,))
            
            articles_data = cursor.fetchall()
            
            # 2. Construir links_data con relevancia y ordenar por relevancia
            links_data = []
            best_image_url = None
            
            for row in articles_data:
                article_id = row[0]
                relevance = article_relevance_scores.get(article_id, 50.0) if article_relevance_scores else 50.0
                
                article_link = {
                    "url": row[1],
                    "source": row[2],
                    "publication_date": row[3].isoformat() if row[3] else None,
                    "title": row[4],
                    "image_url": row[5],
                    "relevance_score": round(relevance, 1)
                }
                links_data.append(article_link)
                
                # Usar imagen del artículo más relevante (o el primero con imagen)
                if not best_image_url and row[5]:
                    best_image_url = row[5]
            
            # Ordenar por relevancia descendente
            links_data.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # 3. Usar imagen real del artículo más relevante
            main_image = best_image_url if best_image_url else topic.main_image_url

            # 4. Insertar Tópico con jerarquía de 5 niveles
            insert_topic_query = """
                INSERT INTO topics (
                    title, summary, main_image_url, priority, category, 
                    subcategory, topic_theme, topic_subtema, country, tags, event_date,
                    article_links, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()) 
                RETURNING id;
            """
            cursor.execute(insert_topic_query, (
                topic.title, 
                topic.summary, 
                main_image,  # Usar imagen real del artículo más relevante
                topic.priority, 
                topic.category,
                topic.subcategory,
                topic.topic_theme,
                topic.topic_subtema,  # Nivel 4
                topic.country,
                topic.tags,  # Formato "#tag,#tag,#tag"
                topic.event_date,
                json.dumps(links_data)
            ))
            new_topic_id = cursor.fetchone()[0]

            # 5. Actualizar Artículos
            update_articles_query = """
                UPDATE articles SET topic_id = %s WHERE id = ANY(%s);
            """
            cursor.execute(update_articles_query, (new_topic_id, article_ids))
            
            conn.commit()
            
            # Log con información de relevancia y jerarquía completa
            avg_relevance = sum(x['relevance_score'] for x in links_data) / len(links_data) if links_data else 0
            hierarchy = f"{topic.category} → {topic.subcategory} → {topic.topic_theme}"
            if topic.topic_subtema and topic.topic_subtema != "General":
                hierarchy += f" → {topic.topic_subtema}"
            print(f"✓ Tópico #{new_topic_id} creado: {hierarchy} [{topic.country}] ({len(article_ids)} artículos, relevancia: {avg_relevance:.1f}%)")
        
        except Exception as e:
            conn.rollback()
            print(f"✗ Error en transacción de guardado: {e}")
        finally:
            cursor.close()
            conn.close()

    def update_article_tags(self, article_id: int, tags: List[str]):
        """Actualiza los tags de un artículo específico"""
        conn = psycopg2.connect(self.conn_string)
        cursor = conn.cursor()
        
        try:
            # Convertir tags a formato JSON array para columna jsonb
            import json
            tags_json = json.dumps(tags) if tags else json.dumps([])
            
            cursor.execute("""
                UPDATE articles 
                SET tags = %s::jsonb 
                WHERE id = %s;
            """, (tags_json, article_id))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"✗ Error actualizando tags del artículo {article_id}: {e}")
        finally:
            cursor.close()
            conn.close()

    def fetch_articles_with_tags(self) -> List[Article]:
        """Obtiene artículos que tienen tags pero no están asignados a un topic"""
        conn = psycopg2.connect(self.conn_string)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, description, url, content_code, category, source, publication_date, tags
            FROM articles 
            WHERE topic_id IS NULL 
            AND tags IS NOT NULL 
            AND jsonb_array_length(tags) > 0
            ORDER BY publication_date DESC;
        """)
        
        articles = []
        for row in cursor.fetchall():
            # Crear Article usando el modelo correcto de src/core/domain.py
            # El modelo tiene: id, title, description, content_code, url, category, source, tags, published_at
            article = Article(
                id=row[0],
                title=row[1],
                description=row[2],
                content_code=row[4],
                url=row[3],
                category=row[5] or "General",
                source=row[6],
                tags=row[8] if row[8] else [],
                published_at=str(row[7]) if row[7] else None
            )
            articles.append(article)
        
        cursor.close()
        conn.close()
        return articles

    def save_cluster(self, temp_title: str, category: str, country: str, 
                     event_date, tags: List[str], article_ids: List[int]) -> int:
        """
        Guarda un cluster (pre-topic) sin título final.
        Retorna el ID del cluster creado.
        """
        conn = psycopg2.connect(self.conn_string)
        cursor = conn.cursor()
        
        try:
            # Convertir tags a formato tag1,tag2
            tags_str = ",".join(tags) if tags else ""
            
            # Crear topic temporal
            cursor.execute("""
                INSERT INTO topics (
                    title, category, country, tags, event_date, 
                    article_links, priority, is_final, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW()) 
                RETURNING id;
            """, (
                temp_title,
                category,
                country,
                tags_str,
                event_date,
                json.dumps([]),  # Links vacíos por ahora
                3,  # Priority por defecto (1: Gigante, 2-3: Importante, 4: Secundario)
                False  # Marcar como no final
            ))
            
            cluster_id = cursor.fetchone()[0]
            
            # Asociar artículos al cluster
            cursor.execute("""
                UPDATE articles 
                SET topic_id = %s 
                WHERE id = ANY(%s);
            """, (cluster_id, article_ids))
            
            conn.commit()
            return cluster_id
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Error guardando cluster: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    def fetch_clusters_without_titles(self) -> List[dict]:
        """Obtiene clusters que necesitan título final (is_final = false)"""
        conn = psycopg2.connect(self.conn_string)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.id, t.title, t.category, t.country, t.tags, t.event_date,
                   array_agg(a.id) as article_ids
            FROM topics t
            LEFT JOIN articles a ON a.topic_id = t.id
            WHERE t.is_final = false OR t.is_final IS NULL
            GROUP BY t.id, t.title, t.category, t.country, t.tags, t.event_date
            ORDER BY t.created_at DESC;
        """)
        
        clusters = []
        for row in cursor.fetchall():
            tags_str = row[4] or ""
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            
            clusters.append({
                'id': row[0],
                'temp_title': row[1],
                'category': row[2],
                'country': row[3],
                'tags': tags,
                'event_date': row[5],
                'article_ids': row[6] or []
            })
        
        cursor.close()
        conn.close()
        return clusters

    def fetch_articles_by_ids(self, article_ids: List[int]) -> List[Article]:
        """Obtiene artículos por sus IDs"""
        if not article_ids:
            return []
        
        conn = psycopg2.connect(self.conn_string)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, description, url, content_code, category, source, publication_date
            FROM articles 
            WHERE id = ANY(%s)
            ORDER BY publication_date DESC;
        """, (article_ids,))
        
        articles = [
            Article(
                id=row[0], 
                title=row[1], 
                description=row[2], 
                content_code=row[3],
                url=row[4],
                category=row[5] or "General",
                source=row[6],
                published_at=row[7]
            ) 
            for row in cursor.fetchall()
        ]
        
        cursor.close()
        conn.close()
        return articles

    def update_cluster_with_title(self, cluster_id: int, title: str, 
                                  category: str, subcategory: str, 
                                  theme: str, subtema: str):
        """Actualiza un cluster con su título final y categorización completa"""
        conn = psycopg2.connect(self.conn_string)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE topics 
                SET title = %s,
                    category = %s,
                    subcategory = %s,
                    topic_theme = %s,
                    topic_subtema = %s,
                    is_final = true
                WHERE id = %s;
            """, (title, category, subcategory, theme, subtema, cluster_id))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"✗ Error actualizando cluster {cluster_id}: {e}")
        finally:
            cursor.close()
            conn.close()