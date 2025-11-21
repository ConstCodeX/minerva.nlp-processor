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

    def save_new_topic(self, topic: TopicData, article_ids: List[int]):
        """Guarda el tópico con categorización jerárquica y actualiza los artículos en una transacción."""
        conn = psycopg2.connect(self.conn_string)
        conn.autocommit = False # Inicia la transacción
        cursor = conn.cursor()
        
        try:
            # 1. Obtener datos completos de los artículos (incluyendo imágenes)
            cursor.execute("""
                SELECT a.url, a.source, a.publication_date, a.title,
                       (SELECT i.url FROM images i WHERE i.article_id = a.id LIMIT 1) as image_url
                FROM articles a
                WHERE a.id = ANY(%s);
            """, (article_ids,))
            
            links_data = [
                {
                    "url": row[0],
                    "source": row[1],
                    "publication_date": row[2].isoformat() if row[2] else None,
                    "title": row[3],
                    "image_url": row[4]
                }
                for row in cursor.fetchall()
            ]

            # 2. Insertar Tópico con nuevos campos jerárquicos
            insert_topic_query = """
                INSERT INTO topics (
                    title, summary, main_image_url, priority, category, 
                    subcategory, topic_theme, country, tags, event_date,
                    article_links, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()) 
                RETURNING id;
            """
            cursor.execute(insert_topic_query, (
                topic.title, 
                topic.summary, 
                topic.main_image_url, 
                topic.priority, 
                topic.category,
                topic.subcategory,
                topic.topic_theme,
                topic.country,
                topic.tags,  # Formato "#tag,#tag,#tag"
                topic.event_date,
                json.dumps(links_data)
            ))
            new_topic_id = cursor.fetchone()[0]

            # 3. Actualizar Artículos
            update_articles_query = """
                UPDATE articles SET topic_id = %s WHERE id = ANY(%s);
            """
            cursor.execute(update_articles_query, (new_topic_id, article_ids))
            
            conn.commit()
            print(f"✓ Tópico #{new_topic_id} creado: {topic.category} → {topic.subcategory} → {topic.topic_theme} [{topic.country}] ({len(article_ids)} artículos)")
        
        except Exception as e:
            conn.rollback()
            print(f"✗ Error en transacción de guardado: {e}")
        finally:
            cursor.close()
            conn.close()