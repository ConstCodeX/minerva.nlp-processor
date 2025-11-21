-- Migration: Agregar columna is_final para soporte de procesamiento por etapas
-- Fecha: 2025-11-21
-- Propósito: Permitir guardar clusters temporales antes de generar títulos finales

-- Agregar columna is_final (indica si el topic tiene título final)
ALTER TABLE topics 
ADD COLUMN IF NOT EXISTS is_final BOOLEAN DEFAULT true;

-- Agregar índice para búsquedas rápidas de topics sin finalizar
CREATE INDEX IF NOT EXISTS idx_topics_is_final 
ON topics(is_final) 
WHERE is_final = false;

-- Agregar columna tags en articles si no existe (para caché de tags extraídos)
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS tags TEXT;

-- Agregar índice para búsquedas de artículos con tags
CREATE INDEX IF NOT EXISTS idx_articles_tags 
ON articles(tags) 
WHERE tags IS NOT NULL;

-- Comentarios
COMMENT ON COLUMN topics.is_final IS 'Indica si el topic tiene título final generado por IA (true) o es un cluster temporal (false)';
COMMENT ON COLUMN articles.tags IS 'Tags extraídos del artículo en formato: #tag1,#tag2,#tag3';
