#!/usr/bin/env python3
"""
Aplica la migración 008 para soporte de procesamiento por etapas
"""

from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()

def apply_migration():
    conn_string = os.environ.get("NEON_CONN_STRING")
    
    if not conn_string:
        print("❌ Error: NEON_CONN_STRING no configurado")
        return
    
    print("=" * 70)
    print("🔧 APLICANDO MIGRACIÓN 008: Procesamiento por Etapas")
    print("=" * 70)
    print()
    
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    
    try:
        print("📝 Agregando columna is_final a topics...")
        cursor.execute("""
            ALTER TABLE topics 
            ADD COLUMN IF NOT EXISTS is_final BOOLEAN DEFAULT true;
        """)
        
        print("📝 Creando índice para topics sin finalizar...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_topics_is_final 
            ON topics(is_final) 
            WHERE is_final = false;
        """)
        
        print("📝 Agregando columna tags a articles...")
        cursor.execute("""
            ALTER TABLE articles 
            ADD COLUMN IF NOT EXISTS tags TEXT;
        """)
        
        print("📝 Creando índice para artículos con tags...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_tags 
            ON articles(tags) 
            WHERE tags IS NOT NULL;
        """)
        
        print("📝 Agregando comentarios...")
        cursor.execute("""
            COMMENT ON COLUMN topics.is_final IS 'Indica si el topic tiene título final generado por IA (true) o es un cluster temporal (false)';
        """)
        cursor.execute("""
            COMMENT ON COLUMN articles.tags IS 'Tags extraídos del artículo en formato: #tag1,#tag2,#tag3';
        """)
        
        conn.commit()
        
        print()
        print("=" * 70)
        print("✅ MIGRACIÓN 008 APLICADA EXITOSAMENTE")
        print("=" * 70)
        print()
        print("📌 Ahora puedes usar el procesamiento por etapas:")
        print("   1. python3 main_step1_tags.py")
        print("   2. python3 main_step2_clustering.py")
        print("   3. python3 main_step3_titles.py")
        print()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error aplicando migración: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    apply_migration()
