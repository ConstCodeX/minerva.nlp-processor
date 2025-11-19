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

    def cluster_and_categorize(self, articles: List[Article]) -> List[TopicData]:
        if not articles:
            return []
            
        df = pd.DataFrame([a.__dict__ for a in articles])
        # Combina título y descripción para el vectorizador
        df['text_combined'] = df['title'] + ' ' + df['description'].fillna('')
        df['processed_text'] = df['text_combined'].apply(self.preprocess)

        # 1. Agrupamiento (Clustering) usando TF-IDF y K-Means
        vectorizer = TfidfVectorizer(max_features=1000)
        X = vectorizer.fit_transform(df['processed_text'])
        
        # ⚠️ Simplificación: Asume 5 tópicos principales para el lote
        num_clusters = min(5, len(articles) // 5) # Asegura al menos 5 artículos por tópico para un cluster
        if num_clusters == 0:
            return []
            
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        df['cluster'] = kmeans.fit_predict(X)
        
        # 2. Generación de Tópico por Cluster (Lógica de Resumen/Prioridad Simplificada)
        processed_topics: List[TopicData] = []
        for cluster_id in df['cluster'].unique():
            cluster_articles = df[df['cluster'] == cluster_id]
            
            # Título y Resumen: Usa el título del artículo más largo como representativo.
            best_article = cluster_articles.loc[cluster_articles['title'].str.len().idxmax()]
            
            # Categoría: Simplificación, usar la categoría más común si la tuviéramos o asignarla
            # En un sistema real, usarías un modelo de clasificación pre-entrenado aquí.
            category = "General" 
            if "economía" in best_article['title'].lower():
                category = "Economía"
            elif "política" in best_article['title'].lower():
                 category = "Política"

            # Prioridad: Simplificación, los clusters grandes son más importantes
            priority = 1 if len(cluster_articles) >= 5 else 3 # Prioridad 1 para tópicos grandes

            # ⚠️ La URL de la imagen se asume ficticia ya que no se extrajo aquí
            main_image_url = f"https://cdn.minerva.ai/topic_{cluster_id}.jpg"

            processed_topics.append(TopicData(
                topic_id=cluster_id, # Usamos el ID del cluster temporalmente
                title=f"TÓPICO CONSOLIDADO: {best_article['title']}",
                summary=f"RESUMEN (Placeholder): Este tópico incluye {len(cluster_articles)} artículos. {best_article['description'][:100]}...",
                main_image_url=main_image_url,
                priority=priority,
                category=category
            ))

        return processed_topics