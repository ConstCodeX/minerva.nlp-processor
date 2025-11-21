# 🤖 Minerva NLP Processor - IA Local

Procesador de artículos de noticias con **IA completamente local** usando Hugging Face Transformers.

## ✨ Características

- ✅ **100% Gratis**: Sin API keys, sin costos
- ✅ **Sin límites**: No hay rate limits
- ✅ **Offline**: Funciona sin internet después de la primera descarga
- ✅ **GitHub Actions**: Compatible sin configuración extra
- ✅ **Categorización inteligente**: 5 niveles jerárquicos con IA
- ✅ **Extracción de entidades**: NER automático
- ✅ **Compatible con Mac**: Probado en macOS con chip Apple Silicon

## 🚀 Quick Start

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar base de datos
cp .env.example .env
# Editar .env y agregar NEON_CONN_STRING

# 3. Aplicar migración (agregar columnas para procesamiento por etapas)
psql $NEON_CONN_STRING -f migrations/migration_008_staged_processing.sql

# 4. Probar IA local (descarga modelos ~600MB)
python3 test_local_ai.py
```

**Nota**: Primera ejecución descarga modelos (~600MB), luego funciona offline.

## 🔄 Procesamiento por Etapas (Recomendado)

El procesamiento se divide en 3 pasos independientes para mejor visibilidad:

### **Paso 1: Extracción de Tags** 
```bash
python3 main_step1_tags.py
```
- Lee artículos sin procesar
- Extrae tags con IA local (NER)
- Guarda tags en BD
- Muestra progreso con barra en tiempo real

### **Paso 2: Clustering de Artículos**
```bash
python3 main_step2_clustering.py
```
- Agrupa artículos similares por tags compartidos
- Discrimina por país y fecha
- Valida mínimo 2 fuentes diferentes
- Crea pre-topics (clusters) en BD

### **Paso 3: Generación de Títulos**
```bash
python3 main_step3_titles.py
```
- Analiza cada cluster con IA
- Genera título único y descriptivo
- Extrae categorización jerárquica completa
- Finaliza topics en BD

### Ejemplo de ejecución:
```bash
# Procesar todo en secuencia
python3 main_step1_tags.py && \
python3 main_step2_clustering.py && \
python3 main_step3_titles.py
```

## 🚀 Procesamiento Directo (Alternativa)

Si prefieres procesar todo de una vez:

```bash
python3 main.py
```

Este comando ejecuta todo el pipeline sin pausas (útil para GitHub Actions).

## 🤖 IA 100% Local

### Modelos Utilizados

- **MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7** (~558MB)
  - Zero-shot classification multilingüe
  - Entiende español perfectamente
  - Categorización jerárquica (Categoría → Subcategoría → Theme → Subtema)
  
- **dslim/bert-base-NER** (~433MB)
  - Named Entity Recognition
  - Extracción automática de nombres, organizaciones, lugares

### Ventajas

- **$0 costo**: Sin API keys, sin suscripciones
- **Sin límites de rate**: Procesa miles de artículos sin restricciones
- **Privacidad total**: Datos nunca salen de tu servidor
- **Reproducible**: Mismos modelos = mismos resultados
- **GitHub Actions**: Descarga modelos automáticamente

## ⚡ Rendimiento

- **Primera ejecución**: 5-10 min (descarga modelos)
- **Procesamiento**: ~2-3 segundos por artículo
- **Almacenamiento**: ~1GB (modelos en caché)
- **RAM**: ~4GB recomendado
- **Costo**: $0.00 para siempre

## 📊 Arquitectura

```
┌─────────────────────────────────────────────────┐
│         LocalHuggingFaceAdapter                 │
│                                                 │
│  ┌──────────────────┐  ┌──────────────────┐   │
│  │   mDeBERTa v3    │  │  BERT-base NER   │   │
│  │  Zero-Shot NLI   │  │  Entity Extract  │   │
│  └──────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────┘
              ↓                     ↓
  ┌─────────────────────┐  ┌─────────────────┐
  │ Categorization Svc  │  │ Tag Extract Svc │
  └─────────────────────┘  └─────────────────┘
              ↓                     ↓
         ┌────────────────────────────┐
         │      NLP Adapter           │
         │  (Orchestrates Services)   │
         └────────────────────────────┘
                    ↓
         ┌────────────────────┐
         │  Processing Service │
         └────────────────────┘
```

## 🆚 Comparación con otras soluciones

| Solución | Costo | Rate Limit | Offline | Setup | Probado |
|----------|-------|------------|---------|-------|---------|
| **IA Local (HF)** | **$0** | **Sin límite** | ✅ | Automático | ✅ Mac M1/M2 |
| Groq API | $0 | 30 RPM | ❌ | API key | ❌ Rate limits |
| OpenAI GPT-4 | $900/mes | Varía | ❌ | API key+$$ | - |
| Ollama | $0 | Sin límite | ✅ | Docker+VM | ❌ No en GH Actions |

## 🔍 Ejemplo de Uso

```python
from src.adapters.local_ai_adapter import AIServiceFactory

# Crear adaptador local
ai_adapter = AIServiceFactory.create_adapter("local")

# Categorizar artículo
category, subcategory, theme, subtema = ai_adapter.categorize_article(
    title="Dina Boluarte reúne al Consejo de Ministros",
    description="La presidenta discutió sobre seguridad ciudadana",
    base_category="Política"
)

# Extraer entidades
entities = ai_adapter.extract_entities(
    text="Dina Boluarte se reunió con Pedro Castillo"
)
# Resultado: ["Boluarte", "Castillo"]
```

## 📝 Próximos Pasos

1. ✅ Modelos descargados y funcionando
2. ✅ Test exitoso en Mac
3. ⏳ Optimizar batch processing para 1000+ artículos
4. ⏳ Integrar con GitHub Actions
5. ⏳ Deploy automático

## 🐛 Troubleshooting

**Error: Bus error en Mac**
- Solución: Ya implementado - usar `TOKENIZERS_PARALLELISM=false`

**Descarga lenta**
- Normal en primera ejecución (~600MB)
- Siguientes ejecuciones usan caché local

**RAM insuficiente**
- Mínimo 4GB recomendado
- Cerrar otras aplicaciones pesadas

## 📄 Licencia

MIT
