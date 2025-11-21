# Categorización con IA 🤖

## Descripción

El procesador NLP ahora soporta **categorización inteligente con IA** usando GPT de OpenAI, reemplazando la lógica rígida de `if/else` con un sistema flexible y adaptable.

## Características

- ✨ **Categorización de 5 niveles** con comprensión contextual
- 🎯 **Extracción de entidades nombradas** automática
- 🔄 **Fallback automático** a reglas si la IA no está disponible
- 💰 **Modelo eficiente**: usa `gpt-4o-mini` por defecto (rápido y económico)
- 📊 **Respuestas estructuradas** en JSON

## Configuración

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar API Key de OpenAI

Agregar a tu archivo `.env`:

```bash
OPENAI_API_KEY=sk-...tu-api-key...
OPENAI_MODEL=gpt-4o-mini  # Opcional, por defecto usa gpt-4o-mini
```

### 3. Ejecutar

```bash
python main.py
```

El sistema detectará automáticamente si tienes una API key configurada:
- ✅ **Con API key**: Usa IA para categorización
- 📋 **Sin API key**: Usa reglas tradicionales (fallback)

## Ventajas de usar IA

### Antes (reglas rígidas):
```python
if 'betsy chávez' in text or 'betsy chavez' in text:
    theme = "Betsy Chávez"
    if 'ministro' in text or 'cultura' in text:
        subtema = "Gestión Ministerial"
```
- ❌ Requiere agregar cada caso manualmente
- ❌ No entiende contexto
- ❌ Difícil de mantener con cientos de reglas

### Ahora (IA):
```python
category, subcategory, theme, subtema = ai_service.categorize_article(
    title="Betsy Chávez asume nuevo cargo en el Ministerio",
    description="La exministra...",
    category="Política"
)
# Resultado: ("Política", "Gabinete Ministerial", "Betsy Chávez", "Gestión Ministerial")
```
- ✅ Entiende contexto y matices
- ✅ Reconoce nuevas entidades sin código adicional
- ✅ Adaptable a noticias cambiantes
- ✅ Fácil de mantener

## Costos estimados

Usando `gpt-4o-mini`:
- **Input**: $0.150 / 1M tokens
- **Output**: $0.600 / 1M tokens
- **Promedio por artículo**: ~500 tokens = $0.0004 USD
- **1,000 artículos**: ~$0.40 USD
- **10,000 artículos**: ~$4.00 USD

💡 **Tip**: Si quieres reducir costos aún más, puedes:
1. Cachear resultados para artículos similares
2. Usar la IA solo para categorías difíciles
3. Procesar en batch para mayor eficiencia

## Ejemplos de categorización

### Política
```json
{
  "titulo": "Dina Boluarte renueva su gabinete ministerial",
  "resultado": {
    "categoria": "Política",
    "subcategoria": "Gabinete Ministerial",
    "tema": "Dina Boluarte",
    "subtema": "Renovación de Gabinete"
  }
}
```

### Espectáculos
```json
{
  "titulo": "Miss Perú avanza a la final de Miss Universo 2024",
  "resultado": {
    "categoria": "Espectáculos",
    "subcategoria": "Concursos de Belleza",
    "tema": "Miss Universo",
    "subtema": "Miss Perú"
  }
}
```

### Deportes
```json
{
  "titulo": "Paolo Guerrero anota doblete en eliminatorias",
  "resultado": {
    "categoria": "Deportes",
    "subcategoria": "Selección Nacional",
    "tema": "Paolo Guerrero",
    "subtema": "Eliminatorias"
  }
}
```

## Desactivar IA

Si quieres forzar el uso de reglas tradicionales:

```python
# En nlp_adapter.py o config
nlp_adapter = NLPAdapter(use_ai=False)
```

O simplemente no configures la API key en `.env`.

## Monitoreo

El sistema mostrará en consola qué modo está usando:

```
✨ Servicio de IA activado para categorización
```

o

```
📋 Usando categorización basada en reglas
```

## Próximas mejoras

- [ ] Cache de resultados para evitar llamadas duplicadas
- [ ] Batch processing para reducir costos
- [ ] Fine-tuning de modelo específico para noticias peruanas
- [ ] Métricas de calidad de categorización
