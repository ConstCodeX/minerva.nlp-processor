"""
Servicio de IA para categorización inteligente de noticias usando modelo local con Ollama.
Reemplaza la lógica rígida de if/else con clasificación basada en LLM local.

VENTAJAS DE OLLAMA LOCAL:
- ✅ 100% gratis (sin costos por API)
- ✅ Rápido (sin latencia de red)
- ✅ Privacidad (datos no salen del servidor)
- ✅ Sin límites de rate (procesa miles de artículos)
"""

import json
from typing import Tuple, List, Optional
import ollama
from src.config.settings import AI_MODEL


class AICategorizationService:
    """Servicio para categorización inteligente usando Ollama (local)"""
    
    def __init__(self):
        """
        Inicializa el servicio con Ollama local
        Modelos recomendados: llama3.1, mistral, qwen2.5
        """
        self.model = AI_MODEL
        
        # Verificar que Ollama esté corriendo y el modelo disponible
        try:
            models = ollama.list()
            available = [m['name'] for m in models.get('models', [])]
            
            if self.model not in available:
                print(f"⚠️ Modelo {self.model} no encontrado. Modelos disponibles: {available}")
                print(f"💡 Ejecuta: ollama pull {self.model}")
                raise Exception(f"Modelo {self.model} no disponible")
                
            print(f"✅ Ollama conectado - Modelo: {self.model}")
        except Exception as e:
            print(f"❌ Error conectando con Ollama: {e}")
            print("💡 Asegúrate de tener Ollama instalado y corriendo:")
            print("   - macOS: brew install ollama && ollama serve")
            print("   - Linux: curl https://ollama.ai/install.sh | sh && ollama serve")
            raise
        
        # Prompt del sistema con la estructura de categorización
        self.system_prompt = """Eres un experto clasificador de noticias peruanas. Tu tarea es categorizar noticias en una jerarquía de 5 niveles.

NIVELES DE CATEGORIZACIÓN:
1. CATEGORÍA (nivel más amplio): Política, Economía, Deportes, Internacional, Tecnología, Espectáculos, Cultura, Salud, Educación, Seguridad, Medio Ambiente, Otro
2. SUBCATEGORÍA: División específica dentro de la categoría
3. TEMA: Tema principal o entidad central de la noticia
4. SUBTEMA: Aspecto específico del tema
5. TÍTULO: Se genera aparte (no incluir aquí)

CATEGORÍAS Y SUBCATEGORÍAS VÁLIDAS:

**Política:**
- Presidente, Congreso, Gobierno Regional, Gobierno Local, Gabinete Ministerial, Poderes del Estado, Elecciones, Partidos Políticos

**Economía:**
- Inflación y Precios, Empleo, Comercio Exterior, Sector Minero, Sector Agrícola, Banca y Finanzas, Empresas

**Deportes:**
- Fútbol Nacional, Fútbol Internacional, Selección Peruana, Otros Deportes

**Espectáculos:**
- Farándula, Concursos de Belleza, Música, Cine y TV, Polémicas

**Cultura:**
- Arte, Literatura, Cine, Teatro, Patrimonio, Festivales

**Internacional:**
- América Latina, Estados Unidos, Europa, Asia, Conflictos, Diplomacia

**Seguridad:**
- Criminalidad, Narcotráfico, Desastres Naturales, Accidentes

**Salud:**
- COVID-19, Sistema de Salud, Epidemias, Medicinas

**Educación:**
- Universidades, Colegios, Reforma Educativa

**Tecnología:**
- Innovación, Startups, Telecomunicaciones

INSTRUCCIONES:
- Para TEMA: identifica la entidad principal (persona, institución, evento)
- Para SUBTEMA: identifica el aspecto específico (puede ser "General" si no hay aspecto específico)
- Usa contexto peruano: reconoce políticos, instituciones, eventos locales
- Si no estás seguro, usa categorías generales

Responde SOLO en formato JSON:
{
  "categoria": "Política",
  "subcategoria": "Presidente",
  "tema": "Dina Boluarte",
  "subtema": "Controversias"
}"""

    def categorize_article(self, title: str, description: str, category: str) -> Tuple[str, str, str, str]:
        """
        Categoriza un artículo usando IA
        
        Args:
            title: Título del artículo
            description: Descripción/contenido del artículo
            category: Categoría inicial (del scraper)
            
        Returns:
            Tuple[categoria, subcategoria, tema, subtema]
        """
        try:
            # Construir el prompt del usuario
            user_prompt = f"""Categoriza esta noticia peruana:

TÍTULO: {title}

DESCRIPCIÓN: {description[:500]}

CATEGORÍA INICIAL: {category}

Responde en JSON con los 4 niveles: categoria, subcategoria, tema, subtema"""

            # Llamar a Ollama local
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.3,  # Baja temperatura para respuestas consistentes
                    "num_predict": 150,   # Máximo de tokens
                },
                format="json"  # Forzar respuesta JSON
            )
            
            # Parsear la respuesta
            result = json.loads(response['message']['content'])
            
            categoria = result.get("categoria", category)
            subcategoria = result.get("subcategoria", "General")
            tema = result.get("tema", "Noticias")
            subtema = result.get("subtema", "General")
            
            return categoria, subcategoria, tema, subtema
            
        except Exception as e:
            print(f"❌ Error en categorización IA: {e}")
            # Fallback a categoría original
            return category, "General", "Noticias", "General"
    
    def categorize_batch(self, articles: List[dict], category: str) -> List[Tuple[str, str, str, str]]:
        """
        Categoriza múltiples artículos en batch (más eficiente)
        
        Args:
            articles: Lista de artículos con 'title' y 'description'
            category: Categoría inicial
            
        Returns:
            Lista de tuplas (categoria, subcategoria, tema, subtema)
        """
        results = []
        
        # Por ahora procesamos uno por uno, pero se puede optimizar con batch API
        for article in articles:
            result = self.categorize_article(
                article.get('title', ''),
                article.get('description', ''),
                category
            )
            results.append(result)
        
        return results
    
    def extract_entities(self, title: str, description: str) -> List[str]:
        """
        Extrae entidades nombradas (personas, instituciones) usando IA
        
        Args:
            title: Título del artículo
            description: Descripción del artículo
            
        Returns:
            Lista de entidades relevantes
        """
        try:
            prompt = f"""Extrae las entidades nombradas más importantes de esta noticia peruana (personas, instituciones, organizaciones, lugares).

TÍTULO: {title}
DESCRIPCIÓN: {description[:500]}

Responde con un JSON con lista de entidades:
{{"entidades": ["Entidad 1", "Entidad 2", ...]}}"""

            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un experto en extracción de entidades nombradas de noticias peruanas."},
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": 0.1,
                    "num_predict": 100,
                },
                format="json"
            )
            
            result = json.loads(response['message']['content'])
            return result.get("entidades", [])
            
        except Exception as e:
            print(f"❌ Error en extracción de entidades: {e}")
            return []
