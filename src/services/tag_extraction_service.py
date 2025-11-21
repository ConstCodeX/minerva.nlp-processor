"""
Servicio de extracción de tags/entidades - Maneja la identificación de entidades nombradas
Responsabilidad única: Extraer tags relevantes de artículos
"""

from typing import List
from src.core.domain import Article
from src.adapters.local_ai_adapter import AIServiceAdapter


class TagExtractionService:
    """Servicio para extraer tags/entidades de artículos"""
    
    def __init__(self, ai_adapter: AIServiceAdapter = None):
        self.ai_adapter = ai_adapter
        
        # Lista compacta de entidades más importantes (fallback)
        self.entity_fallback = [
            # Políticos clave
            'dina boluarte', 'pedro castillo', 'keiko fujimori', 'donald trump', 'biden',
            # Deportes clave
            'paolo guerrero', 'messi', 'alianza lima', 'universitario',
            # Farándula clave
            'magaly medina', 'gisela valcárcel',
            # Eventos clave
            'mundial', 'miss universo', 'congreso',
        ]
    
    def extract(self, article: Article) -> List[str]:
        """
        Extrae tags/entidades de un artículo
        
        Returns:
            Lista de tags normalizados
        """
        # Intentar con IA primero
        if self.ai_adapter and self.ai_adapter.is_available():
            try:
                entities = self.ai_adapter.extract_entities(
                    article.title,
                    article.description or ""
                )
                if entities:
                    return [e.replace(' ', '_').lower() for e in entities][:15]
            except Exception as e:
                print(f"⚠️ Error extrayendo entidades: {e}")
        
        # Fallback: búsqueda básica en lista
        text = f"{article.title} {article.description or ''}".lower()
        tags = []
        
        for entity in self.entity_fallback:
            if entity in text:
                tags.append(entity.replace(' ', '_'))
        
        return list(set(tags))[:15]
