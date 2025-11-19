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

@dataclass
class TopicData:
    """Modelo de Tópico Procesado (Output)"""
    topic_id: str
    title: str
    summary: str
    main_image_url: str
    priority: int
    category: str
    # article_links será manejado por el adaptador de DB como JSONB