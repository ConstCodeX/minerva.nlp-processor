"""
Adapter LOCAL para clasificación de artículos usando modelos de Hugging Face.
Sin API keys, sin límites, completamente offline después de la primera descarga.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
import os


class AIServiceAdapter(ABC):
    """Interfaz abstracta para servicios de IA"""
    
    @abstractmethod
    def categorize_article(self, title: str, description: str, base_category: str) -> Tuple[str, str, str, str]:
        """Categoriza un artículo en la jerarquía de 5 niveles"""
        pass
    
    @abstractmethod
    def extract_entities(self, title: str, description: str) -> List[str]:
        """Extrae entidades nombradas del texto"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el servicio está disponible"""
        pass


class LocalHuggingFaceAdapter(AIServiceAdapter):
    """
    Implementación LOCAL usando Hugging Face Transformers.
    - Sin API keys
    - Sin límites de rate
    - Funciona offline después de la primera descarga
    - Perfecto para GitHub Actions
    """
    
    def __init__(self):
        self._available = False
        self.categorizer = None
        self.ner_pipeline = None
        
        try:
            from transformers import pipeline
            import torch
            
            print("🤖 Inicializando modelos locales de Hugging Face...")
            
            # Modelo para categorización de texto (multilingual)
            # Usamos un modelo pequeño y rápido para clasificación zero-shot
            self.categorizer = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",  # Modelo que entiende español
                device=0 if torch.cuda.is_available() else -1  # GPU si está disponible
            )
            
            # Modelo para extracción de entidades (NER)
            self.ner_pipeline = pipeline(
                "ner",
                model="dslim/bert-base-NER",  # Modelo ligero para NER
                device=0 if torch.cuda.is_available() else -1
            )
            
            self._available = True
            print("✅ Modelos locales listos (sin límites, sin API keys)")
            
        except ImportError:
            print("❌ Instalar: pip install transformers torch")
            self._available = False
        except Exception as e:
            print(f"❌ Error inicializando modelos: {e}")
            self._available = False
    
    def categorize_article(self, title: str, description: str, base_category: str) -> Tuple[str, str, str, str]:
        """Categoriza usando zero-shot classification"""
        if not self.is_available():
            raise Exception("Modelos locales no disponibles")
        
        text = f"{title}. {description or ''}"[:512]  # Límite del modelo
        
        # Categorías principales
        categories = [
            "Política", "Deportes", "Espectáculos", "Economía", 
            "Sociedad", "Cultura", "Tecnología", "Internacional",
            "Salud", "Educación", "Seguridad", "Medio Ambiente"
        ]
        
        # Subcategorías por categoría principal
        subcategories_map = {
            "Política": ["Poder Ejecutivo", "Congreso", "Elecciones", "Corrupción", "Gobierno Regional"],
            "Deportes": ["Fútbol Nacional", "Fútbol Internacional", "Otros Deportes", "Selección Peruana"],
            "Espectáculos": ["Farándula", "Cine", "Música", "Televisión", "Teatro"],
            "Economía": ["Finanzas", "Empresas", "Mercados", "Empleo", "Impuestos"],
        }
        
        try:
            # Paso 1: Clasificar categoría principal
            result = self.categorizer(text, categories, multi_label=False)
            category = result['labels'][0] if result['scores'][0] > 0.3 else base_category
            
            # Paso 2: Clasificar subcategoría
            subcategories = subcategories_map.get(category, ["General"])
            subcat_result = self.categorizer(text, subcategories, multi_label=False)
            subcategory = subcat_result['labels'][0] if subcat_result['scores'][0] > 0.3 else "General"
            
            # Paso 3: Extraer tema principal (primeras palabras clave del título)
            theme = self._extract_theme(title)
            
            # Paso 4: Subtema (basado en palabras clave del texto)
            subtema = self._extract_subtema(description or title)
            
            return (category, subcategory, theme, subtema)
            
        except Exception as e:
            print(f"⚠️ Error en categorización local: {e}")
            return (base_category, "General", "General", "General")
    
    def extract_entities(self, title: str, description: str) -> List[str]:
        """Extrae entidades usando NER local"""
        if not self.is_available():
            raise Exception("Modelos locales no disponibles")
        
        text = f"{title}. {description or ''}"[:512]
        
        try:
            # Extraer entidades con NER
            entities = self.ner_pipeline(text)
            
            # Filtrar y limpiar entidades
            entity_names = []
            for entity in entities:
                if entity['score'] > 0.8:  # Solo entidades con alta confianza
                    name = entity['word'].replace('##', '').strip()
                    if len(name) > 2:
                        entity_names.append(name.lower().replace(' ', '_'))
            
            # Eliminar duplicados y retornar top 10
            return list(set(entity_names))[:10]
            
        except Exception as e:
            print(f"⚠️ Error en extracción de entidades: {e}")
            return []
    
    def _extract_theme(self, title: str) -> str:
        """Extrae el tema principal del título (primeras 3-4 palabras significativas)"""
        words = title.split()
        # Filtrar palabras cortas y stopwords
        significant = [w for w in words if len(w) > 3][:3]
        return ' '.join(significant) if significant else "General"
    
    def _extract_subtema(self, text: str) -> str:
        """Extrae subtema (palabras clave del texto)"""
        words = text.split()
        significant = [w for w in words if len(w) > 4][:2]
        return ' '.join(significant) if significant else "General"
    
    def is_available(self) -> bool:
        return self._available and self.categorizer is not None


class AIServiceFactory:
    """Factory para crear el adapter apropiado"""
    
    @staticmethod
    def create_adapter(provider: str = "local", **kwargs) -> AIServiceAdapter:
        """
        Crea un adapter según el proveedor especificado
        
        Args:
            provider: 'local' (Hugging Face, recomendado y gratuito)
        """
        if provider.lower() == "local":
            return LocalHuggingFaceAdapter()
        else:
            raise ValueError(f"Proveedor no soportado: {provider}. Usa: local")
