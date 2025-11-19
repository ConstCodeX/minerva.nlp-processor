# src/core/ports.py
from abc import ABC, abstractmethod
from typing import List
from .domain import Article, TopicData

# Puerto para la Base de Datos (IRepository)
class ArticleRepository(ABC):
    @abstractmethod
    def fetch_unprocessed_articles(self) -> List[Article]:
        pass

    @abstractmethod
    def save_new_topic(self, topic: TopicData, article_ids: List[int]):
        """Guarda el nuevo tópico y actualiza los artículos con el topic_id."""
        pass

# Puerto para Servicios de Clasificación (INLPService)
class NLPService(ABC):
    @abstractmethod
    def cluster_and_categorize(self, articles: List[Article]) -> List[TopicData]:
        """Aplica clustering, categorización, resumen y asigna prioridad."""
        pass