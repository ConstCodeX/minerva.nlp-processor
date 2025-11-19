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

    def extract_tags(self, article: Article) -> List[str]:
        """
        Extrae tags/entidades importantes del artículo para mejor agrupación.
        Identifica nombres propios, lugares, organizaciones, eventos específicos.
        """
        text = f"{article.title} {article.description or ''}".lower()
        tags = []
        
        # Entidades importantes - nombres propios comunes en noticias peruanas
        entities = [
            # Políticos
            'dina boluarte', 'pedro castillo', 'keiko fujimori', 'martín vizcarra', 'ollanta humala',
            'alberto fujimori', 'alejandro toledo', 'rafael lópez aliaga', 'verónika mendoza',
            'antauro humala', 'vladimir cerrón', 'gino ríos',
            
            # Internacional
            'donald trump', 'joe biden', 'xi jinping', 'vladimir putin', 'volodímir zelenski',
            'javier milei', 'lula da silva', 'gustavo petro', 'nicolás maduro',
            'benjamin netanyahu', 'isaac herzog',
            
            # Deportes
            'paolo guerrero', 'gianluca lapadula', 'andré carrillo', 'yoshimar yotún',
            'edison flores', 'christian cueva', 'luis advíncula', 'renato tapia',
            'alianza lima', 'universitario', 'sporting cristal', 'melgar', 'cienciano',
            'lionel messi', 'cristiano ronaldo', 'neymar', 'kylian mbappé',
            
            # Lugares específicos
            'lima', 'callao', 'arequipa', 'cusco', 'trujillo', 'piura', 'iquitos',
            'machu picchu', 'línea 2', 'panamericana', 'evitamiento', 'aeropuerto jorge chávez',
            
            # Eventos/Temas específicos
            'mundial 2026', 'copa américa', 'elecciones 2026', 'referéndum',
            'estado de emergencia', 'toque de queda', 'copa libertadores', 'champions league',
            'euro 2024', 'juegos olímpicos', 'miss universo',
            
            # Instituciones
            'congreso', 'poder judicial', 'tribunal constitucional', 'fiscalía', 'minsa',
            'sunat', 'bcr', 'banco central', 'indecopi', 'essalud', 'sunafil',
            
            # Empresas/Organizaciones
            'petro-perú', 'latam', 'interbank', 'bcp', 'bbva', 'scotiabank',
            
            # Temas específicos
            'covid-19', 'coronavirus', 'vacuna', 'ómicron', 'bitcoin', 'criptomoneda',
            'inteligencia artificial', 'chatgpt', 'openai', 'netflix', 'disney+',
            'tiktok', 'instagram', 'facebook', 'twitter', 'whatsapp',
            
            # Eventos naturales
            'sismo', 'terremoto', 'temblor', 'tsunami', 'huracán', 'inundación',
            'deslizamiento', 'fenómeno del niño', 'niño costero',
            
            # Deportivos específicos
            'liga 1', 'premier league', 'la liga', 'bundesliga', 'serie a',
            'selección peruana', 'blanquirroja', 'bicolor',
        ]
        
        # Buscar entidades en el texto
        for entity in entities:
            if entity in text:
                # Normalizar el tag
                tag = entity.replace(' ', '_')
                tags.append(tag)
        
        # Extraer palabras clave importantes (sustantivos, nombres)
        words = text.split()
        important_words = []
        
        for i, word in enumerate(words):
            # Detectar palabras capitalizadas (posibles nombres propios)
            if len(word) > 4 and word not in SPANISH_STOPWORDS:
                # Si la palabra aparece al inicio de una frase o es nombre propio
                if i == 0 or (i > 0 and words[i-1] in ['.', ':', '-']):
                    important_words.append(word)
                # Palabras significativas largas
                elif len(word) > 6:
                    important_words.append(word)
        
        # Agregar las top 5 palabras importantes como tags
        tags.extend(important_words[:5])
        
        # Eliminar duplicados y retornar
        return list(set(tags))[:15]  # Máximo 15 tags por artículo

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
        Procesa artículos con agrupación inteligente basada en TAGS:
        1. Extrae tags de cada artículo
        2. Agrupa por tags compartidos (tema específico)
        3. Valida que haya al menos 2 fuentes diferentes
        4. Crea topics solo si cumplen los criterios
        """
        if not articles:
            return []
        
        print(f"📝 Procesando {len(articles)} artículos...")
        
        # Estructuras para almacenar topics por categoría
        # {category: [(title, summary, tags, article_ids, sources)]}
        topics_by_category = {}
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
            if len(tags_set) < 2:
                discarded += 1
                continue
            
            # 4. Obtener fuente del artículo
            source = article.source if hasattr(article, 'source') and article.source else "unknown"
            
            # 5. Inicializar categoría si no existe
            if category not in topics_by_category:
                topics_by_category[category] = []
            
            # 6. Buscar topic similar basado en TAGS COMPARTIDOS
            best_match_idx = -1
            best_similarity = 0
            best_shared_tags = 0
            
            for i, (topic_title, topic_summary, topic_tags, article_ids, sources) in enumerate(topics_by_category[category]):
                # Similitud basada en TAGS compartidos
                shared_tags = tags_set & topic_tags
                num_shared = len(shared_tags)
                
                if num_shared == 0:
                    continue
                
                # Calcular similitud: tags compartidos / total de tags únicos
                total_tags = len(tags_set | topic_tags)
                similarity = num_shared / total_tags if total_tags > 0 else 0
                
                # Priorizar topics con muchos tags compartidos importantes
                # Un tag compartido importante vale más que varios genéricos
                if num_shared >= 2 and similarity > best_similarity:
                    best_similarity = similarity
                    best_match_idx = i
                    best_shared_tags = num_shared
            
            # Si hay un match fuerte (>= 2 tags compartidos Y similitud > 30%), agrupar
            if best_match_idx >= 0 and best_shared_tags >= 2 and best_similarity >= 0.3:
                # Agregar al topic más similar
                topic_title, topic_summary, topic_tags, article_ids, sources = topics_by_category[category][best_match_idx]
                updated_tags = topic_tags | tags_set  # Unir tags
                updated_sources = sources | {source}  # Agregar fuente
                topics_by_category[category][best_match_idx] = (
                    topic_title,
                    topic_summary,
                    updated_tags,
                    article_ids + [article.id],
                    updated_sources
                )
            else:
                # 7. Si no hay similar, crear nuevo topic candidato
                topic_title = article.title
                topic_summary = article.description[:200] if article.description else article.title
                
                topics_by_category[category].append((
                    topic_title,
                    topic_summary,
                    tags_set,
                    [article.id],
                    {source}  # Set de fuentes
                ))
        
        print(f"  ⊗ Artículos descartados (sin tags relevantes/spam): {discarded}")
        
        # 7. Convertir a TopicData - SOLO topics con 2+ fuentes diferentes
        processed_topics: List[TopicData] = []
        topic_id_counter = 0
        min_sources_required = 2  # Mínimo 2 fuentes diferentes
        min_articles_per_topic = 2  # Mínimo 2 artículos
        rejected_single_source = 0
        rejected_single_article = 0
        
        for category, topics_list in topics_by_category.items():
            for topic_title, topic_summary, tags, article_ids, sources in topics_list:
                # Rechazar si no tiene suficientes artículos
                if len(article_ids) < min_articles_per_topic:
                    rejected_single_article += len(article_ids)
                    continue
                
                # VALIDACIÓN CRÍTICA: Rechazar si no tiene al menos 2 fuentes diferentes
                if len(sources) < min_sources_required:
                    rejected_single_source += len(article_ids)
                    continue  # NO crear topic si solo 1 medio lo publicó
                
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
        
        print(f"\n📊 Resultado: {len(processed_topics)} topics creados (validados con múltiples fuentes)")
        print(f"📊 Artículos rechazados (una sola fuente): {rejected_single_source}")
        print(f"📊 Artículos únicos (sin agrupar): {rejected_single_article}")
        print(f"📊 Categorías: {', '.join(topics_by_category.keys())}")
        return processed_topics