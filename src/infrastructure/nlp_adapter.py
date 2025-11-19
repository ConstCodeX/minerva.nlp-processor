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

    def extract_keywords(self, text: str, n=8) -> set:
        """Extrae palabras clave más importantes del texto."""
        words = text.lower().split()
        # Filtrar palabras muy comunes y stopwords
        words = [w for w in words if len(w) > 3 and w not in SPANISH_STOPWORDS]
        # Tomar las primeras N palabras únicas más significativas
        return set(words[:n])

    def quick_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud rápida basada en palabras clave compartidas."""
        keywords1 = self.extract_keywords(text1, 10)
        keywords2 = self.extract_keywords(text2, 10)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Similitud de Jaccard: intersección / unión
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        return intersection / union if union > 0 else 0.0

    def cluster_and_categorize(self, articles: List[Article]) -> List[TopicData]:
        """
        Procesa artículos de forma inteligente y RÁPIDA:
        1. Categoriza cada artículo
        2. Verifica relevancia
        3. Agrupa por similitud de keywords (rápido)
        4. Crea topics solo para grupos significativos
        """
        if not articles:
            return []
        
        print(f"📝 Procesando {len(articles)} artículos...")
        
        # Estructuras para almacenar topics por categoría
        topics_by_category = {}  # {category: [(title, summary, keywords, article_ids)]}
        discarded = 0
        
        # Procesar cada artículo
        for idx, article in enumerate(articles):
            if (idx + 1) % 100 == 0:
                print(f"  Procesados: {idx + 1}/{len(articles)}...")
            
            # 1. Verificar relevancia
            if not self.is_relevant(article):
                discarded += 1
                continue
            
            # 2. Usar categoría ya asignada (no recategorizar)
            category = article.category if hasattr(article, 'category') and article.category else "General"
            
            # 3. Extraer keywords (rápido)
            text_combined = f"{article.title} {article.description or ''}"
            processed_text = self.preprocess(text_combined)
            keywords = self.extract_keywords(processed_text, 10)
            
            # 4. Inicializar categoría si no existe
            if category not in topics_by_category:
                topics_by_category[category] = []
            
            # 5. Buscar topic similar (similitud por keywords compartidas)
            best_match_idx = -1
            best_similarity = 0
            
            for i, (topic_title, topic_summary, topic_keywords, article_ids) in enumerate(topics_by_category[category]):
                # Similitud basada en keywords compartidas (muy rápido)
                shared = len(keywords & topic_keywords)
                
                if len(keywords) == 0:
                    continue
                    
                # Usar similitud basada solo en compartidos / min de los dos sets
                # Esto agrupa de forma más agresiva
                similarity = shared / min(len(keywords), len(topic_keywords)) if min(len(keywords), len(topic_keywords)) > 0 else 0
                
                # Buscar el mejor match
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_idx = i
            
            # Si hay un match razonable (> 20% de keywords compartidas), agrupar
            if best_similarity >= 0.25 and best_match_idx >= 0:
                # Agregar al topic más similar
                topic_title, topic_summary, topic_keywords, article_ids = topics_by_category[category][best_match_idx]
                updated_keywords = topic_keywords | keywords  # Unir keywords
                topics_by_category[category][best_match_idx] = (
                    topic_title,
                    topic_summary,
                    updated_keywords,
                    article_ids + [article.id]
                )
            else:
                # 6. Si no hay similar, crear nuevo topic
                topic_title = article.title
                topic_summary = article.description[:200] if article.description else article.title
                
                topics_by_category[category].append((
                    topic_title,
                    topic_summary,
                    keywords,
                    [article.id]
                ))
        
        print(f"  ⊗ Artículos descartados (irrelevantes): {discarded}")
        
        # 7. Convertir a TopicData (SOLO topics con 2+ artículos = eventos reales)
        processed_topics: List[TopicData] = []
        topic_id_counter = 0
        min_articles_per_topic = 2  # Mínimo 2 artículos para crear un topic
        single_articles = 0
        
        for category, topics_list in topics_by_category.items():
            for topic_title, topic_summary, _, article_ids in topics_list:
                if len(article_ids) < min_articles_per_topic:
                    single_articles += len(article_ids)
                    continue  # Saltar artículos únicos (no son topics reales)
                
                # Determinar prioridad basada en cantidad de artículos
                if len(article_ids) >= 20:
                    priority = 1  # Gigante
                elif len(article_ids) >= 10:
                    priority = 2  # Importante
                elif len(article_ids) >= 5:
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
        
        print(f"\n📊 Resultado: {len(processed_topics)} topics creados (eventos reales con 2+ artículos)")
        print(f"📊 Artículos únicos (no agrupados): {single_articles}")
        print(f"📊 Categorías: {', '.join(topics_by_category.keys())}")
        return processed_topics