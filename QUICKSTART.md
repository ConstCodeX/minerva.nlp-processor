# 🚀 Quick Start: IA Gratis con Groq

## ⚡ Setup Rápido (3 minutos)

### 1. Obtener API Key (gratis)
```bash
# Abre en tu navegador
https://console.groq.com

# Regístrate (GitHub/Google)
# API Keys → Create → Copiar key
```

### 2. Instalar y Configurar
```bash
cd minerva.nlp-processor

# Instalar
pip install groq

# Configurar (reemplaza con tu key)
echo "GROQ_API_KEY=gsk_tu_key_aqui" >> .env
```

### 3. Probar
```bash
python3 test_refactoring.py
```

Deberías ver:
```
✅ Groq adapter inicializado (GRATIS)
✨ IA activada: groq
```

## ☁️ GitHub Actions

### Agregar Secret
1. GitHub → Settings → Secrets → Actions
2. New secret: `GROQ_API_KEY` = tu key
3. Actions → Process News Articles → Run workflow

¡Listo! 🎉

## 💰 ¿Por qué Groq?

- ✅ **$0.00** (vs OpenAI $60-900/mes)
- ✅ **15x más rápido** que OpenAI
- ✅ **6,000 requests/día gratis**
- ✅ Perfecto para GitHub Actions

## 📚 Más Info

- Guía detallada: `GROQ_SETUP.md`
- Arquitectura: `REFACTORING_GUIDE.md`
- Groq Console: https://console.groq.com
