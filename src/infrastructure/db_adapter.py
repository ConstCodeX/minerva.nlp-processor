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
        """Obtiene artículos sin topic_id asignado con su categoría."""
        conn = psycopg2.connect(self.conn_string)
        cursor = conn.cursor()
        
        # Obtiene TODOS los artículos sin procesar (sin topic_id) con categoría
        cursor.execute("""
            SELECT id, title, description, url, content_code, category 
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
                category=row[5] or "General"  # Si no tiene categoría, asignar General
            ) 
            for row in cursor.fetchall()
        ]
        cursor.close()
        conn.close()
        return articles

    def save_new_topic(self, topic: TopicData, article_ids: List[int]):
        """Guarda el tópico y actualiza los artículos en una transacción."""
        conn = psycopg2.connect(self.conn_string)
        conn.autocommit = False # Inicia la transacción
        cursor = conn.cursor()
        
        try:
            # 1. Obtener URLs reales de los artículos
            cursor.execute("""
                SELECT url, source, publication_date 
                FROM articles 
                WHERE id = ANY(%s);
            """, (article_ids,))
            
            links_data = [
                {
                    "url": row[0],
                    "source": row[1],
                    "publication_date": row[2].isoformat() if row[2] else None
                }
                for row in cursor.fetchall()
            ]

            # 2. Insertar Tópico
            insert_topic_query = """
                INSERT INTO topics (title, summary, main_image_url, priority, category, article_links, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW()) RETURNING id;
            """
            cursor.execute(insert_topic_query, (
                topic.title, 
                topic.summary, 
                topic.main_image_url, 
                topic.priority, 
                topic.category, 
                json.dumps(links_data)
            ))
            new_topic_id = cursor.fetchone()[0]

            # 3. Actualizar Artículos
            update_articles_query = """
                UPDATE articles SET topic_id = %s WHERE id = ANY(%s);
            """
            cursor.execute(update_articles_query, (new_topic_id, article_ids))
            
            conn.commit()
            print(f"Tópico #{new_topic_id} creado y {len(article_ids)} artículos actualizados.")
        
        except Exception as e:
            conn.rollback()
            print(f"Error en transacción de guardado: {e}")
        finally:
            cursor.close()
            conn.close()