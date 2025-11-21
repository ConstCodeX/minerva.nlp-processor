#!/usr/bin/env python3
"""
Script de prueba para IA local con Hugging Face
"""
import os
from src.core.domain import Article
from src.infrastructure.nlp_adapter import NLPAdapter
from datetime import datetime

def test_local_ai():
    print("🧪 Probando IA LOCAL con Hugging Face...\n")
    print("📦 Primera vez descargará modelos (~500MB), luego funciona offline\n")
    
    # Artículo de prueba
    article = Article(
        id="test-1",
        title="Dina Boluarte se reúne con el Congreso sobre la crisis política",
        description="La presidenta discutió temas de gobernabilidad con los legisladores",
        content_code=None,
        url="http://test.com",
        category="Política",
        source="test",
        tags=[],
        published_at=datetime.now().isoformat()
    )
    
    # Crear adaptador con IA local
    print("1️⃣ Inicializando IA local...")
    nlp = NLPAdapter(use_ai=True)
    
    if not nlp.categorization_service.ai_adapter:
        print("\n❌ IA local no disponible")
        print("💡 Instala dependencias: pip install transformers torch")
        return
    
    # Probar categorización
    print("\n2️⃣ Probando categorización...")
    category, subcategory, theme, subtema = nlp.extract_hierarchical_category(article, "Política")
    print(f"   ✓ Category: {category}")
    print(f"   ✓ Subcategory: {subcategory}")
    print(f"   ✓ Theme: {theme}")
    print(f"   ✓ Subtema: {subtema}")
    
    # Probar extracción de tags
    print("\n3️⃣ Probando extracción de entidades...")
    tags = nlp.extract_tags(article)
    print(f"   ✓ Tags: {tags}")
    
    # Probar detección de país
    print("\n4️⃣ Probando detección de país...")
    country = nlp.detect_country(article.title + " " + (article.description or ""))
    print(f"   ✓ País: {country}")
    
    print("\n✅ Pruebas completadas!")
    print("\n💡 Ventajas de IA local:")
    print("   - Sin API keys")
    print("   - Sin límites de rate")
    print("   - 100% gratis")
    print("   - Funciona offline")
    print("   - Perfecto para GitHub Actions")

if __name__ == "__main__":
    test_local_ai()
