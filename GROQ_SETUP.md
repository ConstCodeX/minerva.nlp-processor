# 🚀 Guía: IA GRATIS para GitHub Actions con Groq

## 🎯 ¿Por qué Groq?

### ✅ Ventajas
- **100% GRATIS**: Sin tarjeta de crédito
- **Ultra-rápido**: 750+ tokens/segundo (vs 40-60 de OpenAI)
- **Generoso**: 30 requests/minuto, 6000/día (suficiente para miles de artículos)
- **Sin instalación**: API REST (vs Ollama que necesita Docker/servidor)
- **Perfecto para GitHub Actions**: Solo necesitas una API key

### ❌ Alternativas y sus problemas
- **Ollama**: Necesita servidor siempre corriendo (no funciona en GitHub Actions)
- **OpenAI**: Pago ($0.002-0.03 por request)
- **Claude**: Pago ($0.003-0.015 por request)

## 📝 Paso 1: Obtener API Key de Groq (2 minutos)

1. Ve a: https://console.groq.com
2. Regístrate con GitHub/Google (gratis, sin tarjeta)
3. Ve a "API Keys" → "Create API Key"
4. Copia la key (empieza con `gsk_`)

Ejemplo: `gsk_abc123xyz456def789ghi012jkl345mno678pqr901stu234vwx567yz`

## 🔧 Paso 2: Configurar Localmente

```bash
# 1. Instalar dependencias
cd minerva.nlp-processor
pip install groq

# 2. Crear archivo .env
cp .env.example .env

# 3. Editar .env y agregar tu API key
# GROQ_API_KEY=gsk_tu_key_aqui
```

## 🧪 Paso 3: Probar Localmente

```bash
# Probar que funciona
cd minerva.nlp-processor
python3 -c "
from src.infrastructure.nlp_adapter import NLPAdapter
from src.core.domain import Article
from datetime import datetime

nlp = NLPAdapter(use_ai=True, ai_provider='groq')

article = Article(
    id='test-1',
    title='Dina Boluarte se reúne con el Congreso por crisis política',
    description='La presidenta busca diálogo con los legisladores',
    content_code=None,
    url='http://test.com',
    category='Política',
    source='test',
    tags=[],
    published_at=datetime.now().isoformat()
)

cat, subcat, theme, subtema = nlp.extract_hierarchical_category(article, 'Política')
print(f'Category: {cat}')
print(f'Subcategory: {subcat}')
print(f'Theme: {theme}')
print(f'Subtema: {subtema}')
"
```

Deberías ver:
```
✅ Groq adapter inicializado (GRATIS)
✨ IA activada: groq
Category: Política
Subcategory: Poder Ejecutivo
Theme: Dina Boluarte
Subtema: Crisis Presidencial
```

## ☁️ Paso 4: Configurar en GitHub Actions

### 4.1 Agregar Secret en GitHub

1. Ve a tu repo en GitHub
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `GROQ_API_KEY`
5. Value: Tu API key de Groq
6. Click "Add secret"

### 4.2 Verificar Workflow

El archivo `.github/workflows/process-news.yml` ya está configurado para usar Groq.

### 4.3 Ejecutar Manualmente (para probar)

1. Ve a: Actions → Process News Articles
2. Click "Run workflow" → "Run workflow"
3. Espera 2-3 minutos
4. Verifica los logs

## 📊 Límites y Costos

### Groq (GRATIS)
```
✅ Límites por día:
   - 6,000 requests/día
   - 30 requests/minuto
   - 10,000 tokens por request

💰 Costo: $0.00 (gratis para siempre)

📈 Suficiente para:
   - 250 artículos/hora = 6,000/día
   - Más que suficiente para un agregador de noticias
```

### Comparación con alternativas

| Proveedor | Costo por 1000 requests | Velocidad | GitHub Actions |
|-----------|-------------------------|-----------|----------------|
| **Groq**  | **$0.00** ✅            | 750 tok/s | ✅ Perfecto    |
| Ollama    | $0.00                   | 40 tok/s  | ❌ Necesita VM |
| OpenAI    | $2.00-$30.00            | 60 tok/s  | ⚠️ Caro        |
| Claude    | $3.00-$15.00            | 80 tok/s  | ⚠️ Caro        |

## 🔄 Cambiar de Proveedor (si lo necesitas)

El código está diseñado para cambiar fácilmente:

```python
# Usar Groq (GRATIS)
nlp = NLPAdapter(use_ai=True, ai_provider="groq")

# Cambiar a Ollama (local)
nlp = NLPAdapter(use_ai=True, ai_provider="ollama")

# Cambiar a OpenAI (pago)
nlp = NLPAdapter(use_ai=True, ai_provider="openai")
```

## 🐛 Troubleshooting

### Error: "GROQ_API_KEY no encontrado"
```bash
# Verificar que existe en .env
cat .env | grep GROQ_API_KEY

# Verificar que se carga
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GROQ_API_KEY'))"
```

### Error: "No module named 'groq'"
```bash
pip install groq
```

### Error: "Rate limit exceeded"
```
⚠️ Llegaste al límite de 30 requests/minuto
💡 Solución: Agregar time.sleep(2) entre requests
```

### GitHub Actions: Workflow no ejecuta
```
1. Verificar que GROQ_API_KEY está en Secrets
2. Verificar que el workflow tiene permisos (Settings → Actions → General)
3. Revisar logs en Actions tab
```

## 📈 Monitoreo de Uso

Ve tu uso en: https://console.groq.com/usage

```
🔍 Podrás ver:
   - Requests por día
   - Tokens consumidos
   - Errores
   - Latencia promedio
```

## 🎉 Ventajas del Sistema

1. **Gratis**: Groq no cobra nada
2. **Rápido**: 750 tokens/segundo (15x más rápido que OpenAI)
3. **Escalable**: 6000 artículos/día
4. **Sin instalación**: Solo API REST
5. **GitHub Actions**: Configuración en 2 minutos
6. **Swappable**: Cambiar a otro proveedor sin cambiar código

## 📝 Ejemplo de Código Completo

```python
# main.py
from src.infrastructure.nlp_adapter import NLPAdapter
from src.core.domain import Article
import os

# Automático: Lee GROQ_API_KEY de .env
nlp = NLPAdapter(use_ai=True, ai_provider="groq")

# Procesar artículo
article = Article(...)
category, subcategory, theme, subtema = nlp.extract_hierarchical_category(
    article, 
    "Política"
)
tags = nlp.extract_tags(article)
country = nlp.detect_country(article.title)

print(f"Categoría: {category}/{subcategory}/{theme}/{subtema}")
print(f"Tags: {tags}")
print(f"País: {country}")
```

## 🔐 Seguridad

- ✅ API key en `.env` (nunca en código)
- ✅ `.env` en `.gitignore` (no subir a GitHub)
- ✅ GitHub Secrets (encriptado)
- ✅ Groq no guarda tus datos

## 📚 Recursos

- Groq Console: https://console.groq.com
- Groq Docs: https://console.groq.com/docs
- Groq Pricing: https://console.groq.com/pricing (gratis)
- GitHub Actions Docs: https://docs.github.com/actions

---

**¿Listo para empezar?**

```bash
# 1. Obtener API key (2 min)
open https://console.groq.com

# 2. Instalar
pip install groq

# 3. Configurar
echo "GROQ_API_KEY=tu_key_aqui" >> .env

# 4. Probar
python3 test_refactoring.py

# 5. Deploy a GitHub
git push

# 6. Configurar Secret en GitHub
# Settings → Secrets → GROQ_API_KEY

# ¡Listo! 🎉
```
