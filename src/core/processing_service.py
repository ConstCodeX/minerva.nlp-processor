# src/core/processing_service.py
from typing import List
from .ports import ArticleRepository, NLPService
from .domain import Article, TopicData

class NewsProcessingService:
    def __init__(self, repository: ArticleRepository, nlp_service: NLPService):
        # Inyección de Dependencias (Puertos)
        self._repository = repository
        self._nlp_service = nlp_service

    def process_and_save_topics(self):
        # 1. Leer artículos crudos (a través del Puerto IRepository)
        articles = self._repository.fetch_unprocessed_articles()
        
        if not articles:
            print("No hay artículos crudos para procesar.")
            return

        print(f"Artículos encontrados: {len(articles)}")
        
        # 2. Procesar (a través del Puerto INLPService)
        processed_topics = self._nlp_service.cluster_and_categorize(articles)
        
        # 3. Guardar los nuevos tópicos y actualizar los artículos
        for topic in processed_topics:
            # Los IDs de artículos vienen directamente del TopicData
            self._repository.save_new_topic(
                topic, 
                topic.article_ids,
                topic.article_relevance_scores
            )