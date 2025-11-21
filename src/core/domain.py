# src/core/domain.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Article:
    """Modelo de Artículo Crudo (Input)"""
    id: str
    title: str
    description: Optional[str]
    content_code: Optional[str]
    url: Optional[str]
    category: str = "General"  # Categoría ya asignada en la BD
    source: str = ""  # Fuente del artículo (elcomercio, la_republica, etc)
    tags: List[str] = None  # Tags/palabras clave extraídas del contenido
    published_at: Optional[str] = None  # Fecha de publicación del artículo

@dataclass
class TopicData:
    """
    Modelo de Tópico Procesado (Output) con categorización jerárquica de 5 niveles:
    
    Nivel 1: category (ej: "Política", "Deportes", "Espectáculos")
    Nivel 2: subcategory (ej: "Presidente", "Fútbol Nacional", "Farándula")
    Nivel 3: topic_theme (ej: "Donald Trump", "Selección Peruana", "Miss Universo")
    Nivel 4: topic_subtema (ej: "Gabinete Ministerial", "Eliminatorias Qatar", "Miss Perú")
    Nivel 5: title (Topic específico generado)
    """
    topic_id: str
    title: str
    summary: str
    main_image_url: str
    priority: int
    category: str  # Nivel 1
    subcategory: str  # Nivel 2
    topic_theme: str  # Nivel 3
    topic_subtema: str  # Nivel 4 - NUEVO
    country: str  # País del evento (ej: "Perú", "USA", "Chile")
    tags: str  # Tags separados por comas: "#trump,#política,#usa,#2025-11-20"
    event_date: str  # Fecha del evento (YYYY-MM-DD)
    article_ids: List[str]  # Lista de IDs de artículos que pertenecen a este topic
    article_relevance_scores: dict = None  # Dict {article_id: relevance_score_percentage}
    # article_links será manejado por el adaptador de DB como JSONB