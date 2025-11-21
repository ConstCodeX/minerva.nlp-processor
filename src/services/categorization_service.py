"""
Servicio de categorización - Maneja la lógica de categorización de artículos
Responsabilidad única: Categorizar artículos usando IA o fallback
"""

from typing import Tuple
from src.core.domain import Article
from src.adapters.local_ai_adapter import AIServiceAdapter


class CategorizationService:
    """Servicio para categorizar artículos en jerarquía de 5 niveles"""
    
    def __init__(self, ai_adapter: AIServiceAdapter = None):
        self.ai_adapter = ai_adapter
    
    def categorize(self, article: Article, base_category: str) -> Tuple[str, str, str, str]:
        """
        Categoriza un artículo en 5 niveles jerárquicos
        
        Returns:
            Tuple[category, subcategory, theme, subtema]
        """
        # Intentar con IA
        if self.ai_adapter and self.ai_adapter.is_available():
            try:
                return self.ai_adapter.categorize_article(
                    article.title,
                    article.description or "",
                    base_category
                )
            except Exception as e:
                print(f"⚠️ Error en categorización IA: {e}")
        
        # Fallback básico
        print(f"⚠️ Usando fallback para: {article.title[:50]}...")
        return (base_category, "General", "General", "General")
