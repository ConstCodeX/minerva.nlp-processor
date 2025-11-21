"""
Adapter para servicios de IA - Interfaz agnóstica que permite cambiar entre diferentes proveedores
(Ollama, OpenAI, Claude, etc.) sin modificar el código del NLP processor.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple


class AIServiceAdapter(ABC):
    """Interfaz abstracta para servicios de IA"""
    
    @abstractmethod
    def categorize_article(self, title: str, description: str, base_category: str) -> Tuple[str, str, str, str]:
        """
        Categoriza un artículo en la jerarquía de 5 niveles
        
        Returns:
            Tuple[category, subcategory, theme, subtema]
        """
        pass
    
    @abstractmethod
    def extract_entities(self, title: str, description: str) -> List[str]:
        """
        Extrae entidades nombradas del texto
        
        Returns:
            Lista de entidades (nombres, lugares, organizaciones)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el servicio está disponible"""
        pass


class OllamaAdapter(AIServiceAdapter):
    """
    [DEPRECATED] Implementación para Ollama (IA local)
    
    RECOMENDACIÓN: Usa GroqAdapter en su lugar (gratis, más rápido, sin instalación)
    Ollama requiere Docker/servidor local y no funciona en GitHub Actions.
    """
    
    def __init__(self):
        print("⚠️ OllamaAdapter está DEPRECATED. Usa GroqAdapter (gratis, más rápido)")
        print("💡 Cambiar a: NLPAdapter(ai_provider='groq')")
        
        try:
            from src.services.ai_categorization import AICategorizationService
            self.service = AICategorizationService()
            self._available = True
            print("✅ Ollama adapter inicializado (considera migrar a Groq)")
        except Exception as e:
            print(f"❌ Error inicializando Ollama: {e}")
            self._available = False
            self.service = None
    
    def categorize_article(self, title: str, description: str, base_category: str) -> Tuple[str, str, str, str]:
        if not self.is_available():
            raise Exception("Ollama no está disponible")
        return self.service.categorize_article(title, description, base_category)
    
    def extract_entities(self, title: str, description: str) -> List[str]:
        if not self.is_available():
            raise Exception("Ollama no está disponible")
        return self.service.extract_entities(title, description)
    
    def is_available(self) -> bool:
        return self._available and self.service is not None


class GroqAdapter(AIServiceAdapter):
    """Implementación para Groq API (GRATIS, ultra-rápido, perfecto para GitHub Actions)"""
    
    def __init__(self, api_key: str = None):
        import os
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self._available = False
        
        if not self.api_key:
            print("⚠️ GROQ_API_KEY no encontrado en variables de entorno")
            return
        
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            # Test connection
            self.client.models.list()
            self._available = True
            print("✅ Groq adapter inicializado (GRATIS)")
        except ImportError:
            print("❌ Instalar: pip install groq")
            self._available = False
        except Exception as e:
            print(f"❌ Error inicializando Groq: {e}")
            self._available = False
    
    def categorize_article(self, title: str, description: str, base_category: str) -> Tuple[str, str, str, str]:
        if not self.is_available():
            raise Exception("Groq no está disponible")
        
        prompt = f"""Analiza este artículo de noticias peruano y categorízalo en 4 niveles jerárquicos.

TÍTULO: {title}
DESCRIPCIÓN: {description or 'N/A'}
CATEGORÍA BASE: {base_category}

Responde SOLO con 4 líneas en este formato exacto:
CATEGORY: [Política|Deportes|Espectáculos|Economía|Sociedad|Cultura|Tecnología|Internacional|Salud|Educación|Seguridad|Medio Ambiente]
SUBCATEGORY: [subcategoría específica]
THEME: [tema principal del artículo]
SUBTEMA: [subtema más específico]

Ejemplos:
- "Dina Boluarte en crisis" → Política | Poder Ejecutivo | Dina Boluarte | Crisis Presidencial
- "Paolo Guerrero anota gol" → Deportes | Fútbol Nacional | Paolo Guerrero | Goles
- "Magaly entrevista a Pamela" → Espectáculos | Farándula | Magaly Medina | Entrevistas"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Gratis, rápido, potente
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            
            text = response.choices[0].message.content.strip()
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            
            category = subcategory = theme = subtema = "General"
            
            for line in lines:
                if line.startswith('CATEGORY:'):
                    category = line.split(':', 1)[1].strip()
                elif line.startswith('SUBCATEGORY:'):
                    subcategory = line.split(':', 1)[1].strip()
                elif line.startswith('THEME:'):
                    theme = line.split(':', 1)[1].strip()
                elif line.startswith('SUBTEMA:'):
                    subtema = line.split(':', 1)[1].strip()
            
            return (category, subcategory, theme, subtema)
        except Exception as e:
            print(f"⚠️ Error en Groq categorización: {e}")
            return (base_category, "General", "General", "General")
    
    def extract_entities(self, title: str, description: str) -> List[str]:
        if not self.is_available():
            raise Exception("Groq no está disponible")
        
        prompt = f"""Extrae SOLO los nombres propios importantes (personas, lugares, organizaciones) de este texto de noticias.

TÍTULO: {title}
DESCRIPCIÓN: {description or 'N/A'}

Responde SOLO con una lista separada por comas, sin explicaciones:
Ejemplo: dina_boluarte, congreso, lima, donald_trump"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=100
            )
            
            text = response.choices[0].message.content.strip()
            entities = [e.strip().lower().replace(' ', '_') for e in text.split(',')]
            return [e for e in entities if e and len(e) > 2][:15]
        except Exception as e:
            print(f"⚠️ Error en Groq extracción: {e}")
            return []
    
    def is_available(self) -> bool:
        return self._available


class OpenAIAdapter(AIServiceAdapter):
    """Implementación para OpenAI (GPT) - Placeholder para implementación futura"""
    
    def __init__(self, api_key: str):
        # TODO: Implementar cuando se necesite OpenAI
        self.api_key = api_key
        self._available = False
    
    def categorize_article(self, title: str, description: str, base_category: str) -> Tuple[str, str, str, str]:
        raise NotImplementedError("OpenAI adapter no implementado aún")
    
    def extract_entities(self, title: str, description: str) -> List[str]:
        raise NotImplementedError("OpenAI adapter no implementado aún")
    
    def is_available(self) -> bool:
        return self._available


class ClaudeAdapter(AIServiceAdapter):
    """Implementación para Claude (Anthropic) - Placeholder para implementación futura"""
    
    def __init__(self, api_key: str):
        # TODO: Implementar cuando se necesite Claude
        self.api_key = api_key
        self._available = False
    
    def categorize_article(self, title: str, description: str, base_category: str) -> Tuple[str, str, str, str]:
        raise NotImplementedError("Claude adapter no implementado aún")
    
    def extract_entities(self, title: str, description: str) -> List[str]:
        raise NotImplementedError("Claude adapter no implementado aún")
    
    def is_available(self) -> bool:
        return self._available


class AIServiceFactory:
    """Factory para crear el adapter apropiado según configuración"""
    
    @staticmethod
    def create_adapter(provider: str = "groq", **kwargs) -> AIServiceAdapter:
        """
        Crea un adapter según el proveedor especificado
        
        Args:
            provider: 'groq' (GRATIS), 'ollama', 'openai', 'claude'
            **kwargs: Argumentos específicos del proveedor (api_key, etc.)
        
        Recomendado para GitHub Actions: 'groq' (gratis, rápido, sin instalación)
        """
        if provider.lower() == "groq":
            api_key = kwargs.get('api_key')
            return GroqAdapter(api_key)
        elif provider.lower() == "ollama":
            return OllamaAdapter()
        elif provider.lower() == "openai":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("OpenAI requiere api_key")
            return OpenAIAdapter(api_key)
        elif provider.lower() == "claude":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("Claude requiere api_key")
            return ClaudeAdapter(api_key)
        else:
            raise ValueError(f"Proveedor no soportado: {provider}. Usa: groq, ollama, openai, claude")
