# src/infrastructure/nlp_adapter.py
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date
from src.core.ports import NLPService
from src.core.domain import Article, TopicData
from src.adapters.ai_adapter import AIServiceFactory
from src.services.categorization_service import CategorizationService
from src.services.tag_extraction_service import TagExtractionService
from src.services.country_detection_service import CountryDetectionService
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import nltk
from nltk.corpus import stopwords
import re
import ssl
import os

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
    def __init__(self, use_ai: bool = True, ai_provider: str = "groq"):
        """
        Inicializa el adaptador NLP con servicios especializados
        
        Args:
            use_ai: Si es True, usa IA. Si es False, usa solo fallbacks
            ai_provider: Proveedor de IA ('groq' [GRATIS], 'ollama', 'openai', 'claude')
        
        Recomendado para GitHub Actions: 'groq' (gratis, sin instalación, ultra-rápido)
        """
        # Inicializar adapter de IA (agnóstico del proveedor)
        ai_adapter = None
        if use_ai:
            try:
                ai_adapter = AIServiceFactory.create_adapter(ai_provider)
                if ai_adapter.is_available():
                    print(f"✨ IA activada: {ai_provider}")
                else:
                    print(f"⚠️ {ai_provider} no disponible, usando fallbacks")
                    ai_adapter = None
            except Exception as e:
                print(f"⚠️ Error inicializando {ai_provider}: {e}")
                ai_adapter = None
        
        # Inicializar servicios especializados (inyección de dependencias)
        self.categorization_service = CategorizationService(ai_adapter)
        self.tag_extraction_service = TagExtractionService(ai_adapter)
        self.country_detection_service = CountryDetectionService()
    
    def preprocess(self, text: str) -> str:
        """Limpieza básica de texto en español."""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text) # Eliminar puntuación
        words = text.split()
        words = [word for word in words if word not in SPANISH_STOPWORDS]
        return " ".join(words)

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

    def detect_country(self, text: str) -> Optional[str]:
        """Detecta el país mencionado en el texto usando el servicio especializado"""
        return self.country_detection_service.detect(text)

    def extract_event_date(self, article: Article) -> Optional[date]:
        """
        Intenta extraer la fecha del evento de la noticia.
        Por defecto usa published_at, pero puede detectar fechas específicas en el texto.
        """
        # Usar la fecha de publicación como fecha del evento
        if hasattr(article, 'published_at') and article.published_at:
            if isinstance(article.published_at, datetime):
                return article.published_at.date()
            elif isinstance(article.published_at, date):
                return article.published_at
        
        # Si no hay fecha, usar hoy
        return date.today()

    def extract_hierarchical_category(self, article: Article, base_category: str) -> Tuple[str, str, str, str]:
        """
        Extrae categorización jerárquica de 5 niveles usando servicio especializado.
        
        Nivel 1 (category): Categoría principal (Política, Deportes, Espectáculos, etc.)
        Nivel 2 (subcategory): Subcategoría específica (Presidente, Fútbol Nacional, Farándula, etc.)
        Nivel 3 (theme): Tema principal (Donald Trump, Selección Peruana, Miss Universo, etc.)
        Nivel 4 (subtema): Subtema específico (Gabinete, Eliminatorias, Concurso Final, etc.)
        Nivel 5 (title): El título único del topic se genera después
        
        Retorna: category, subcategory, theme, subtema
        """
        return self.categorization_service.categorize(article, base_category)
    def extract_tags(self, article: Article) -> List[str]:
        """Extrae tags/entidades importantes usando el servicio especializado"""
        return self.tag_extraction_service.extract(article)

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
        Procesa artículos con agrupación inteligente basada en TAGS + discriminación por país/fecha:
        1. Extrae tags, país y fecha de cada artículo
        2. Agrupa por tags compartidos + mismo país + misma fecha (discriminación inteligente)
        3. Valida que haya al menos 2 fuentes diferentes
        4. Genera categorización jerárquica (category → subcategory → theme)
        5. Crea topics solo si cumplen los criterios
        """
        if not articles:
            return []
        
        print(f"📝 Procesando {len(articles)} artículos...")
        
        # Estructuras para almacenar topics por categoría + país + fecha
        # {(category, country, date): [(title, summary, tags, article_ids, sources, subcategory, theme)]}
        topics_by_key = {}
        discarded = 0
        
        # Procesar cada artículo
        for idx, article in enumerate(articles):
            if (idx + 1) % 100 == 0:
                print(f"  Procesados: {idx + 1}/{len(articles)}...")
            
            # 1. Verificar relevancia
            if not self.is_relevant(article):
                discarded += 1
                continue
            
            # 2. Usar categoría ya asignada
            category = article.category if hasattr(article, 'category') and article.category else "General"
            
            # 3. Extraer TAGS del artículo (entidades, nombres, temas específicos)
            tags = self.extract_tags(article)
            tags_set = set(tags)
            
            # Si no hay tags significativos, saltar
            if len(tags_set) < 2:  # Mínimo 2 tags para asegurar relevancia
                discarded += 1
                continue
            
            # 4. Detectar país y fecha del evento
            text = f"{article.title} {article.description or ''}"
            country = self.detect_country(text)
            event_date = self.extract_event_date(article)
            
            # 5. Extraer categorización jerárquica de 5 niveles
            category_main, subcategory, theme, subtema = self.extract_hierarchical_category(article, category)
            
            # 6. Obtener fuente del artículo
            source = article.source if hasattr(article, 'source') and article.source else "unknown"
            
            # 7. Clave única por categoría + discriminación inteligente
            # SOLO discriminar por país en categorías donde importa el lugar del evento:
            # - General (desastres naturales, eventos locales)
            # - Seguridad (crimen específico de cada país)
            # Para Política/Deportes/Economía internacional, NO discriminar por país
            # (queremos agrupar todas las noticias de Trump, o Messi, sin importar desde dónde se reportan)
            
            discriminate_by_country = category_main in ["General", "Seguridad"]
            
            if discriminate_by_country and country:
                key = (category_main, subcategory, country, event_date)
            else:
                # Para temas internacionales/globales, agrupar solo por categoría+subcategoría
                key = (category_main, subcategory, None, None)
            
            # 8. Inicializar clave si no existe
            if key not in topics_by_key:
                topics_by_key[key] = []
            
            # 9. Buscar topic similar basado en TAGS COMPARTIDOS dentro de esta clave
            best_match_idx = -1
            best_similarity = 0
            best_shared_tags = 0
            
            for i, (topic_title, topic_summary, topic_tags, article_ids, sources, topic_subcategory, topic_theme, topic_subtema) in enumerate(topics_by_key[key]):
                # Similitud basada en TAGS compartidos
                shared_tags = tags_set & topic_tags
                num_shared = len(shared_tags)
                
                if num_shared == 0:
                    continue
                
                # Calcular similitud: tags compartidos / total de tags únicos
                total_tags = len(tags_set | topic_tags)
                similarity = num_shared / total_tags if total_tags > 0 else 0
                
                # Criterios de agrupación más flexibles:
                # - Con 3+ tags compartidos: agrupar si similitud > 15%
                # - Con 2 tags compartidos: agrupar si similitud > 25%
                # Esto permite agrupar mejor noticias relacionadas sin ser demasiado permisivo
                meets_criteria = (
                    (num_shared >= 3 and similarity >= 0.15) or
                    (num_shared >= 2 and similarity >= 0.25)
                )
                
                if meets_criteria and similarity > best_similarity:
                    best_similarity = similarity
                    best_match_idx = i
                    best_shared_tags = num_shared
            
            # Si hay un match válido, agrupar
            if best_match_idx >= 0:
                # Agregar al topic más similar
                topic_title, topic_summary, topic_tags, article_ids, sources, topic_subcategory, topic_theme, topic_subtema = topics_by_key[key][best_match_idx]
                updated_tags = topic_tags | tags_set  # Unir tags
                updated_sources = sources | {source}  # Agregar fuente
                topics_by_key[key][best_match_idx] = (
                    topic_title,
                    topic_summary,
                    updated_tags,
                    article_ids + [article.id],
                    updated_sources,
                    topic_subcategory,  # Mantener subcategoría
                    topic_theme,  # Mantener tema
                    topic_subtema  # Mantener subtema
                )
            else:
                # 10. Si no hay similar, crear nuevo topic candidato
                topic_title = article.title
                topic_summary = article.description[:200] if article.description else article.title
                
                topics_by_key[key].append((
                    topic_title,
                    topic_summary,
                    tags_set,
                    [article.id],
                    {source},  # Set de fuentes
                    subcategory,
                    theme,
                    subtema  # Nivel 4
                ))
        
        print(f"  ⊗ Artículos descartados (sin tags relevantes/spam): {discarded}")
        print(f"  📦 Total de agrupaciones candidatas: {sum(len(topics) for topics in topics_by_key.values())}")
        
        # 11. Convertir a TopicData - Validación flexible balanceada
        processed_topics: List[TopicData] = []
        topic_id_counter = 0
        rejected_low_quality = 0
        
        for (category, subcategory_key, country, event_date), topics_list in topics_by_key.items():
            for topic_title, topic_summary, tags, article_ids, sources, subcategory, theme, subtema in topics_list:
                num_articles = len(article_ids)
                num_sources = len(sources)
                
                # Validación balanceada:
                # - Si tiene 2+ fuentes: acepta incluso con 2 artículos
                # - Si tiene 1 sola fuente: requiere 3+ artículos (evita topics débiles)
                # - Rechaza topics de 1 artículo de 1 fuente (no es topic, es noticia única)
                is_valid_topic = (
                    (num_sources >= 2 and num_articles >= 2) or
                    (num_sources >= 1 and num_articles >= 3)
                )
                
                if not is_valid_topic:
                    rejected_low_quality += num_articles
                    continue
                
                # Determinar prioridad basada en cantidad de artículos Y fuentes
                num_articles = len(article_ids)
                num_sources = len(sources)
                
                # Dar más prioridad a topics con muchas fuentes
                if num_articles >= 20 or num_sources >= 5:
                    priority = 1  # Gigante - noticia muy importante
                elif num_articles >= 10 or num_sources >= 4:
                    priority = 2  # Importante
                elif num_articles >= 5 or num_sources >= 3:
                    priority = 3  # Medio
                else:
                    priority = 4  # Secundario
                
                # Formatear tags como "#tag,#tag,#tag,#country,#date"
                formatted_tags = ','.join([f"#{tag.replace('_', '')}" for tag in sorted(tags)[:10]])
                if country and country != "General":
                    formatted_tags += f",#{country.replace(' ', '')}"
                if event_date:
                    formatted_tags += f",#{event_date.strftime('%Y-%m-%d')}"
                
                # Calcular relevancia de cada artículo en el topic
                article_relevance_scores = self._calculate_article_relevance(article_ids, tags, articles)
                
                # Generar resumen mejorado usando los artículos más relevantes
                enhanced_summary = self._generate_enhanced_summary(
                    article_ids, 
                    article_relevance_scores, 
                    articles,
                    topic_title
                )
                
                processed_topics.append(TopicData(
                    topic_id=str(topic_id_counter),
                    title=topic_title,
                    summary=enhanced_summary,
                    main_image_url=f"https://cdn.minerva.ai/topic_{topic_id_counter}.jpg",
                    priority=priority,
                    category=category,
                    subcategory=subcategory,
                    topic_theme=theme,
                    topic_subtema=subtema,  # Nivel 4
                    country=country if country != "General" else None,
                    tags=formatted_tags,
                    event_date=event_date,
                    article_ids=article_ids,
                    article_relevance_scores=article_relevance_scores
                ))
                topic_id_counter += 1
        
        print(f"\n📊 Resultado: {len(processed_topics)} topics creados (validación balanceada)")
        print(f"📊 Artículos rechazados (baja calidad): {rejected_low_quality}")
        print(f"📊 Claves únicas (categoría+país+fecha): {len(topics_by_key)}")
        print(f"📊 Topics por categoría: {len(topics_by_key)} agrupaciones")
        return processed_topics

    def _calculate_article_relevance(self, article_ids: List[str], topic_tags: set, all_articles: List[Article]) -> dict:
        """
        Calcula el porcentaje de relevancia de cada artículo en el topic.
        
        Factores de relevancia:
        - Tags compartidos con el topic (60%)
        - Posición temporal (20%) - artículos más recientes son más relevantes
        - Tamaño del contenido (20%) - artículos más completos son más relevantes
        
        Returns:
            dict: {article_id: relevance_percentage}
        """
        # Crear lookup de artículos por ID
        articles_dict = {art.id: art for art in all_articles if art.id in article_ids}
        
        if not articles_dict:
            return {}
        
        relevance_scores = {}
        
        # Obtener fechas para calcular recencia
        article_dates = []
        for art_id in article_ids:
            if art_id in articles_dict:
                article = articles_dict[art_id]
                if hasattr(article, 'published_at') and article.published_at:
                    try:
                        from datetime import datetime
                        if isinstance(article.published_at, str):
                            pub_date = datetime.fromisoformat(article.published_at.replace('Z', '+00:00'))
                        else:
                            pub_date = article.published_at
                        article_dates.append((art_id, pub_date))
                    except:
                        pass
        
        # Ordenar por fecha para calcular posición temporal
        article_dates.sort(key=lambda x: x[1], reverse=True)  # Más reciente primero
        
        for art_id in article_ids:
            if art_id not in articles_dict:
                relevance_scores[art_id] = 50.0  # Score por defecto
                continue
            
            article = articles_dict[art_id]
            score = 0.0
            
            # 1. Tags compartidos (60 puntos máximo)
            article_text = f"{article.title} {article.description or ''}".lower()
            article_tags = set(self.extract_tags(article))
            shared_tags = article_tags & topic_tags
            
            if topic_tags:
                tag_similarity = len(shared_tags) / len(topic_tags)
                score += min(tag_similarity * 100, 60.0)  # Máximo 60 puntos
            else:
                score += 30.0  # Score base si no hay tags
            
            # 2. Posición temporal (20 puntos máximo)
            # Artículos más recientes obtienen mayor score
            if article_dates:
                position = next((i for i, (aid, _) in enumerate(article_dates) if aid == art_id), len(article_dates))
                temporal_score = (1 - position / len(article_dates)) * 20
                score += temporal_score
            else:
                score += 10.0  # Score medio si no hay fechas
            
            # 3. Completitud del contenido (20 puntos máximo)
            title_length = len(article.title) if article.title else 0
            desc_length = len(article.description) if article.description else 0
            content_length = title_length + desc_length
            
            # Normalizar: artículos con 500+ caracteres obtienen máximo puntaje
            content_score = min(content_length / 500, 1.0) * 20
            score += content_score
            
            # Asegurar que el score esté entre 0 y 100
            relevance_scores[art_id] = min(max(score, 0.0), 100.0)
        
        return relevance_scores
    
    def _generate_enhanced_summary(self, article_ids: List[str], relevance_scores: dict, 
                                   all_articles: List[Article], topic_title: str) -> str:
        """
        Genera un resumen mejorado usando los artículos más relevantes del topic.
        
        Prioriza artículos con mayor relevancia para construir un resumen más informativo.
        """
        # Crear lookup de artículos
        articles_dict = {art.id: art for art in all_articles if art.id in article_ids}
        
        if not articles_dict:
            return topic_title[:300]
        
        # Ordenar artículos por relevancia
        sorted_articles = sorted(
            article_ids,
            key=lambda aid: relevance_scores.get(aid, 0),
            reverse=True
        )
        
        # Tomar los 3 artículos más relevantes
        top_articles = sorted_articles[:3]
        
        # Construir resumen combinando información de los artículos más relevantes
        summary_parts = []
        seen_content = set()
        
        for art_id in top_articles:
            if art_id not in articles_dict:
                continue
            
            article = articles_dict[art_id]
            
            # Usar descripción si está disponible
            if article.description:
                desc = article.description.strip()
                # Evitar duplicados
                desc_lower = desc.lower()[:100]
                if desc_lower not in seen_content:
                    summary_parts.append(desc)
                    seen_content.add(desc_lower)
            elif article.title and article.title != topic_title:
                title_lower = article.title.lower()[:100]
                if title_lower not in seen_content:
                    summary_parts.append(article.title)
                    seen_content.add(title_lower)
        
        # Combinar los resúmenes
        if summary_parts:
            combined_summary = " ".join(summary_parts)
            # Limitar a 500 caracteres para mantener conciso
            if len(combined_summary) > 500:
                combined_summary = combined_summary[:497] + "..."
            return combined_summary
        
        # Fallback: usar título si no hay descripciones
        return topic_title[:300]