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
            # Aquí necesitarías mapear qué artículos pertenecen a este TopicData
            # En la implementación simplificada, asumimos todos los artículos en el cluster
            # (En un sistema real, esta información de mapeo vendría del NLPAdapter)
            
            # ⚠️ Simplificación: Agrupamos todos los IDs de artículos por cluster
            article_ids_in_topic = [a.id for a in articles] # NECESITA SER REFINADO EN EL NLPAdapter
            
            self._repository.save_new_topic(topic, article_ids_in_topic)