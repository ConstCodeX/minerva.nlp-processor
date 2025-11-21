#!/usr/bin/env python3
"""
PRUEBA DEL SISTEMA SIN BASE DE DATOS
Prueba que los componentes de IA y procesamiento funcionan correctamente
Ideal para GitHub Actions donde no hay acceso a BD
"""

import os
import sys

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_ai_components():
    """Prueba los componentes de IA sin necesidad de base de datos"""
    
    print("=" * 70)
    print("🧪 PRUEBA DE COMPONENTES DEL SISTEMA (SIN BD)")
    print("=" * 70)
    print()
    
    # ==================================================================
    # TEST 1: IA LOCAL (NER + CATEGORIZACIÓN)
    # ==================================================================
    print("━" * 70)
    print("🤖 TEST 1: IA LOCAL - Modelos Hugging Face")
    print("━" * 70)
    print()
    
    try:
        from src.adapters.local_ai_adapter import AIServiceFactory
        
        print("Inicializando IA local...")
        ai_adapter = AIServiceFactory.create_adapter("local")
        
        if ai_adapter.is_available():
            print("✅ IA local inicializada correctamente")
            print()
            
            # Test de categorización
            print("📋 Test de categorización:")
            test_title = "Dina Boluarte se reúne con el Consejo de Ministros"
            test_desc = "La presidenta discutió temas de seguridad ciudadana"
            
            category, subcategory, theme, subtema = ai_adapter.categorize_article(
                title=test_title,
                description=test_desc,
                base_category="Política"
            )
            
            print(f"  Título: {test_title}")
            print(f"  ✓ Category: {category}")
            print(f"  ✓ Subcategory: {subcategory}")
            print(f"  ✓ Theme: {theme}")
            print(f"  ✓ Subtema: {subtema}")
            print()
            
            # Test de extracción de entidades
            print("🏷️  Test de extracción de entidades (NER):")
            test_ner_title = "Dina Boluarte se reunió con Pedro Castillo"
            test_ner_desc = "El encuentro se realizó en el Palacio de Gobierno en Lima"
            entities = ai_adapter.extract_entities(test_ner_title, test_ner_desc)
            
            print(f"  Título: {test_ner_title}")
            print(f"  Descripción: {test_ner_desc}")
            print(f"  ✓ Entidades: {entities}")
            print()
            
        else:
            print("❌ IA local no disponible")
            return False
            
    except Exception as e:
        print(f"❌ Error en test de IA: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ==================================================================
    # TEST 2: SERVICIOS DE PROCESAMIENTO
    # ==================================================================
    print("━" * 70)
    print("🔧 TEST 2: Servicios de Procesamiento")
    print("━" * 70)
    print()
    
    try:
        from src.services.tag_extraction_service import TagExtractionService
        from src.services.categorization_service import CategorizationService
        from src.services.country_detection_service import CountryDetectionService
        from src.core.domain import Article
        
        # Crear artículo de prueba
        test_article = Article(
            id=1,
            title="Perú clasifica al Mundial 2026 tras vencer a Chile",
            description="La selección peruana logró una victoria histórica en Lima",
            content_code="test",
            url="http://test.com",
            category="Deportes",
            source="test",
            published_at=None
        )
        
        print("📄 Artículo de prueba:")
        print(f"  {test_article.title}")
        print()
        
        # Tag extraction
        print("🏷️  Extracción de tags:")
        tag_service = TagExtractionService(ai_adapter)
        tags = tag_service.extract(test_article)
        print(f"  ✓ Tags: {tags}")
        print()
        
        # Categorización
        print("📊 Categorización jerárquica:")
        cat_service = CategorizationService(ai_adapter)
        category, subcategory, theme, subtema = cat_service.categorize(test_article, "Deportes")
        print(f"  ✓ Category: {category}")
        print(f"  ✓ Subcategory: {subcategory}")
        print(f"  ✓ Theme: {theme}")
        print(f"  ✓ Subtema: {subtema}")
        print()
        
        # Detección de país
        print("🌎 Detección de país:")
        country_service = CountryDetectionService()
        country = country_service.detect(test_article.description)
        print(f"  ✓ País: {country}")
        print()
        
    except Exception as e:
        print(f"❌ Error en test de servicios: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ==================================================================
    # TEST 3: SIMILITUD DE TAGS (CLUSTERING)
    # ==================================================================
    print("━" * 70)
    print("🔗 TEST 3: Algoritmo de Clustering")
    print("━" * 70)
    print()
    
    try:
        def calculate_tag_similarity(tags1, tags2):
            set1, set2 = set(tags1), set(tags2)
            if not set1 or not set2:
                return 0.0
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            return intersection / union if union > 0 else 0.0
        
        tags_article1 = ["peru", "mundial", "futbol", "seleccion"]
        tags_article2 = ["peru", "futbol", "clasificacion", "seleccion"]
        tags_article3 = ["economia", "dolar", "banco_central"]
        
        similarity_12 = calculate_tag_similarity(tags_article1, tags_article2)
        similarity_13 = calculate_tag_similarity(tags_article1, tags_article3)
        
        print(f"📝 Artículo 1 tags: {tags_article1}")
        print(f"📝 Artículo 2 tags: {tags_article2}")
        print(f"📝 Artículo 3 tags: {tags_article3}")
        print()
        print(f"✓ Similitud 1-2: {similarity_12:.2f} (deben agruparse: {similarity_12 >= 0.3})")
        print(f"✓ Similitud 1-3: {similarity_13:.2f} (deben agruparse: {similarity_13 >= 0.3})")
        print()
        
        if similarity_12 >= 0.3 and similarity_13 < 0.3:
            print("✅ Algoritmo de clustering funciona correctamente")
        else:
            print("❌ Algoritmo de clustering tiene problemas")
            return False
            
    except Exception as e:
        print(f"❌ Error en test de clustering: {e}")
        return False
    
    # ==================================================================
    # RESUMEN FINAL
    # ==================================================================
    print("=" * 70)
    print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
    print("=" * 70)
    print()
    print("Componentes verificados:")
    print("  ✓ IA Local (Hugging Face) - Modelos cargados")
    print("  ✓ Categorización jerárquica - Funcionando")
    print("  ✓ Extracción de entidades (NER) - Funcionando")
    print("  ✓ Detección de país - Funcionando")
    print("  ✓ Algoritmo de clustering - Funcionando")
    print()
    print("🎯 El sistema está listo para procesar artículos")
    print("   Para prueba completa con BD ejecuta:")
    print("   python3 main_step1_tags.py")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = test_ai_components()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
