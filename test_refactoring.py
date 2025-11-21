#!/usr/bin/env python3
"""
Script de prueba para validar la refactorización del NLPAdapter
"""
import os
from dotenv import load_dotenv
from src.core.domain import Article
from src.infrastructure.nlp_adapter import NLPAdapter
from datetime import datetime

# Cargar variables de entorno desde .env
load_dotenv()

def test_nlp_adapter():
    print("🧪 Probando NLPAdapter refactorizado...\n")
    
    # Crear adaptador (sin IA para prueba rápida)
    nlp = NLPAdapter(use_ai=False)
    
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
    
    # 1. Probar categorización
    print("1️⃣ Probando categorización jerárquica...")
    category, subcategory, theme, subtema = nlp.extract_hierarchical_category(article, "Política")
    print(f"   ✓ Category: {category}")
    print(f"   ✓ Subcategory: {subcategory}")
    print(f"   ✓ Theme: {theme}")
    print(f"   ✓ Subtema: {subtema}\n")
    
    # 2. Probar extracción de tags
    print("2️⃣ Probando extracción de tags...")
    tags = nlp.extract_tags(article)
    print(f"   ✓ Tags encontrados: {tags}\n")
    
    # 3. Probar detección de país
    print("3️⃣ Probando detección de país...")
    country = nlp.detect_country(article.title + " " + (article.description or ""))
    print(f"   ✓ País detectado: {country}\n")
    
    # 4. Probar con IA (Groq - GRATIS) si está disponible
    print("4️⃣ Probando con IA (Groq - GRATIS)...")
    try:
        nlp_ai = NLPAdapter(use_ai=True, ai_provider="groq")
        category_ai, subcategory_ai, theme_ai, subtema_ai = nlp_ai.extract_hierarchical_category(article, "Política")
        print(f"   ✓ IA Category: {category_ai}")
        print(f"   ✓ IA Subcategory: {subcategory_ai}")
        print(f"   ✓ IA Theme: {theme_ai}")
        print(f"   ✓ IA Subtema: {subtema_ai}")
        
        tags_ai = nlp_ai.extract_tags(article)
        print(f"   ✓ IA Tags: {tags_ai}\n")
    except Exception as e:
        print(f"   ⚠️ Groq no disponible: {e}")
        print(f"   💡 Obtén tu API key gratis en: https://console.groq.com\n")
    
    print("✅ Todas las pruebas completadas!")
    print("\n💡 Para usar Groq (GRATIS):")
    print("   1. Regístrate en: https://console.groq.com")
    print("   2. Copia tu API key")
    print("   3. Agrégala a .env: GROQ_API_KEY=tu_key")
    print("   4. Lee la guía completa: cat GROQ_SETUP.md")

if __name__ == "__main__":
    test_nlp_adapter()
