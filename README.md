# Minerva NLP Processor 🧠

Procesador de noticias con categorización inteligente usando IA **100% GRATIS**.

## 🚀 Quick Start (3 minutos)

```bash
# 1. Obtener API key gratis
open https://console.groq.com

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar
echo "GROQ_API_KEY=tu_key_aqui" >> .env

# 4. Probar
python3 test_refactoring.py

# 5. Ejecutar
python3 main.py
```

## 📚 Documentación

- **[QUICKSTART.md](QUICKSTART.md)** - Setup en 3 minutos
- **[GROQ_SETUP.md](GROQ_SETUP.md)** - Guía completa paso a paso
- **[REFACTORING_GUIDE.md](REFACTORING_GUIDE.md)** - Arquitectura y diseño

## 🎯 Características

- ✨ **Categorización con IA gratis** - Groq API (sin costo, ultra-rápido)
- 📊 **5 niveles de categorización** - Categoría → Subcategoría → Tema → Subtema → Título
- 🏷️ **Extracción automática de entidades** - Personas, instituciones, lugares
- 🔄 **Fallback automático** - Si falla la IA, usa valores por defecto
- 💰 **$0.00 de costo** - 6,000 requests/día gratis
- ☁️ **GitHub Actions ready** - Workflow incluido

## 🚀 ¿Por qué Groq?

| Groq (API) | OpenAI (Cloud) | Ollama (Local) |
|------------|----------------|----------------|
| ✅ Gratis | ❌ $60-900/mes | ✅ Gratis |
| ✅ 750 tok/s | ⚠️ 60 tok/s | ⚠️ 40 tok/s |
| ✅ Sin instalación | ✅ Sin instalación | ❌ Requiere Docker |
| ✅ GitHub Actions | ✅ GitHub Actions | ❌ No funciona |
| ✅ 6k requests/día | ❌ Rate limits | ✅ Sin límites |

**💰 Ahorro anual: $720 - $10,800**

## 📈 Rendimiento

Con **Groq (llama-3.3-70b)**:
- **Velocidad**: 750 tokens/segundo
- **Latencia**: ~500ms por artículo
- **Límite**: 6,000 artículos/día (gratis)
- **Costo**: $0.00

## 🔧 Configuración

Variables de entorno (`.env`):

```bash
# Base de datos
DATABASE_URL=postgresql://user:pass@host/db

# Modelo de IA (opcional, por defecto qwen2.5:7b)
AI_MODEL=qwen2.5:7b

# Opciones: qwen2.5:7b, llama3.1:8b, mistral:7b
```

## 💡 Ejemplo de uso

```python
from src.services.ai_categorization import AICategorizationService

ai = AICategorizationService()

categoria, subcategoria, tema, subtema = ai.categorize_article(
    title="Dina Boluarte renueva gabinete ministerial",
    description="La presidenta anunció cambios...",
    category="Política"
)

# Categorizar con IA (Groq)
category, subcategory, theme, subtema = nlp.extract_hierarchical_category(
    article,
    "Política"
)

# Resultado:
# category: "Política"
# subcategory: "Poder Ejecutivo"
# theme: "Dina Boluarte"
# subtema: "Gabinete Ministerial"
```

## 🛠️ Troubleshooting

### Error: "GROQ_API_KEY no encontrado"
```bash
# Verificar .env
cat .env | grep GROQ_API_KEY

# Agregar si no existe
echo "GROQ_API_KEY=tu_key" >> .env
```

### Error: "No module named 'groq'"
```bash
pip install groq
```

### Error: "Rate limit exceeded"
```
⚠️ Límite alcanzado: 30 requests/minuto
💡 Solución: Espera 1 minuto o agrega delay entre requests
```

## 📊 Arquitectura

```
┌─────────────────┐
│   Scraper Job   │ → Artículos crudos en BD
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│    NLP Processor        │
│   ┌───────────────┐     │
│   │  Groq API     │     │ → Categorización con IA
│   │  (GRATIS)     │     │   (750 tokens/seg)
│   └───────────────┘     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│  Topics en BD   │ → 5 niveles categorizados
│  + Tags + País  │
└─────────────────┘
```

## ☁️ GitHub Actions

El proyecto incluye un workflow listo para GitHub Actions:

1. Settings → Secrets → Actions
2. Agregar: `GROQ_API_KEY` = tu key
3. Actions → Process News Articles → Run workflow

El workflow procesará artículos automáticamente cada hora.

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/mejora`)
3. Commit (`git commit -am 'Agrega mejora'`)
4. Push (`git push origin feature/mejora`)
5. Abre un Pull Request

## 📝 Licencia

MIT
