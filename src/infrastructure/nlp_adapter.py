# src/infrastructure/nlp_adapter.py
from typing import List
from src.core.ports import NLPService
from src.core.domain import Article, TopicData
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import nltk
from nltk.corpus import stopwords
import re
import ssl

# Descarga de recursos de NLTK (solo la primera vez)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("Descargando recursos de NLTK...")
    try:
        # Intenta con SSL normal
        nltk.download('stopwords')
        nltk.download('punkt')
    except:
        # Si falla, desactiva verificación SSL (para desarrollo)
        ssl._create_default_https_context = ssl._create_unverified_context
        nltk.download('stopwords')
        nltk.download('punkt')
    
SPANISH_STOPWORDS = set(stopwords.words('spanish'))

class NLPAdapter(NLPService):
    def preprocess(self, text: str) -> str:
        """Limpieza básica de texto en español."""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text) # Eliminar puntuación
        words = text.split()
        words = [word for word in words if word not in SPANISH_STOPWORDS]
        return " ".join(words)

    def categorize_article(self, text: str) -> str:
        """Categoriza un artículo basándose en palabras clave."""
        text_lower = text.lower()
        
        # Política
        if any(word in text_lower for word in ['congreso', 'presidente', 'ministr', 'legisl', 'gobierno', 'elecciones', 'partido', 'dina boluarte', 'castillo', 'fujimori']):
            return "Política"
        
        # Economía
        if any(word in text_lower for word in ['economía', 'dólar', 'inflación', 'banco central', 'bcr', 'precio', 'mercado', 'inversión', 'comercio', 'exportación', 'pbi', 'sunat']):
            return "Economía"
        
        # Seguridad
        if any(word in text_lower for word in ['crimen', 'delincuencia', 'robo', 'asalto', 'policía', 'seguridad', 'extorsión', 'secuestro', 'asesinato', 'homicidio']):
            return "Seguridad"
        
        # Deportes
        if any(word in text_lower for word in ['fútbol', 'deporte', 'selección', 'alianza', 'universitario', 'cristal', 'copa', 'mundial', 'liga', 'gol', 'partido', 'jugador']):
            return "Deportes"
        
        # Salud
        if any(word in text_lower for word in ['salud', 'hospital', 'médico', 'enfermedad', 'vacuna', 'minsa', 'essalud', 'pandemia', 'covid', 'tratamiento']):
            return "Salud"
        
        # Educación
        if any(word in text_lower for word in ['educación', 'universidad', 'colegio', 'estudiante', 'profesor', 'minedu', 'examen', 'admisión']):
            return "Educación"
        
        # Internacional
        if any(word in text_lower for word in ['internacional', 'mundo', 'eeuu', 'china', 'europa', 'rusia', 'brasil', 'argentina', 'venezuela']):
            return "Internacional"
        
        return "General"

    def is_relevant(self, article: Article) -> bool:
        """Determina si un artículo es relevante para procesar."""
        # Filtrar artículos muy cortos o sin contenido significativo
        if not article.title or len(article.title) < 20:
            return False
        
        # Filtrar contenido irrelevante (publicidad, spam, etc.)
        spam_keywords = ['sorteo', 'promoción', 'descuento', 'oferta', 'ganador', 'premio']
        text_lower = (article.title + ' ' + (article.description or '')).lower()
        
        if any(word in text_lower for word in spam_keywords):
            return False
            
        return True

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud entre dos textos usando TF-IDF."""
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = (tfidf_matrix * tfidf_matrix.T).toarray()[0, 1]
            return similarity
        except:
            return 0.0

    def cluster_and_categorize(self, articles: List[Article]) -> List[TopicData]:
        """
        Procesa artículos de forma inteligente:
        1. Categoriza cada artículo
        2. Verifica relevancia
        3. Crea nuevos topics basados en el contenido único
        """
        if not articles:
            return []
        
        processed_topics: List[TopicData] = []
        topics_by_category = {}  # {category: [(title, summary, article_ids)]}
        
        # Procesar cada artículo individualmente
        for article in articles:
            # 1. Verificar relevancia
            if not self.is_relevant(article):
                print(f"  ⊗ Artículo irrelevante descartado: {article.title[:50]}...")
                continue
            
            # 2. Categorizar
            text_combined = f"{article.title} {article.description or ''}"
            category = self.categorize_article(text_combined)
            
            # 3. Preprocesar texto
            processed_text = self.preprocess(text_combined)
            
            # 4. Buscar topic similar existente en la misma categoría
            if category not in topics_by_category:
                topics_by_category[category] = []
            
            found_similar = False
            similarity_threshold = 0.6  # 60% de similitud para agrupar
            
            for i, (topic_title, topic_summary, topic_text, article_ids) in enumerate(topics_by_category[category]):
                similarity = self.calculate_similarity(processed_text, topic_text)
                
                if similarity >= similarity_threshold:
                    # Agregar a topic existente
                    topics_by_category[category][i] = (
                        topic_title,
                        topic_summary,
                        topic_text,
                        article_ids + [article.id]
                    )
                    found_similar = True
                    print(f"  ✓ Artículo agrupado a topic existente ({category}): {article.title[:50]}...")
                    break
            
            # 5. Si no hay similar, crear nuevo topic
            if not found_similar:
                # Usar el título y descripción del artículo como base del topic
                topic_title = article.title
                topic_summary = article.description[:200] if article.description else article.title
                
                topics_by_category[category].append((
                    topic_title,
                    topic_summary,
                    processed_text,
                    [article.id]
                ))
                print(f"  ✓ Nuevo topic creado ({category}): {topic_title[:50]}...")
        
        # 6. Convertir a TopicData
        topic_id_counter = 0
        for category, topics_list in topics_by_category.items():
            for topic_title, topic_summary, _, article_ids in topics_list:
                # Determinar prioridad basada en cantidad de artículos
                if len(article_ids) >= 10:
                    priority = 1  # Gigante
                elif len(article_ids) >= 5:
                    priority = 2  # Importante
                elif len(article_ids) >= 2:
                    priority = 3  # Medio
                else:
                    priority = 4  # Secundario
                
                processed_topics.append(TopicData(
                    topic_id=str(topic_id_counter),
                    title=topic_title,
                    summary=topic_summary,
                    main_image_url=f"https://cdn.minerva.ai/topic_{topic_id_counter}.jpg",
                    priority=priority,
                    category=category,
                    article_ids=article_ids
                ))
                topic_id_counter += 1
        
        print(f"\n📊 Resumen: {len(processed_topics)} topics creados de {len(articles)} artículos")
        return processed_topics